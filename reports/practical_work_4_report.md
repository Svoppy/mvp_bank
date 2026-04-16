# Практическая работа №4

**Тема:** Статический анализ MVP и автоматическое выявление потенциальных уязвимостей  
**Проект:** `mvp_bank` (Django + Django Ninja)

## Цель работы

Провести ручной и автоматический статический анализ текущего MVP, выявить риски безопасности, исправить критичные проблемы и сравнить результаты до/после исправлений.

## Задание 1. Ручной статический анализ MVP

### 1.1 Анализ структуры программы

| Функция / модуль | Назначение | Тип в модели Source → Propagation → Sink |
| --- | --- | --- |
| `apps/auth_app/api.py::login()` | Вход пользователя, выдача JWT | Source + Sink |
| `apps/auth_app/api.py::refresh_tokens()` | Ротация refresh/access токенов | Source + Propagation + Sink |
| `apps/auth_app/services.py::register_login_failure()` | Лимитирование неуспешных логинов | Propagation |
| `core/security.py::decode_token()` | Верификация JWT | Propagation |
| `apps/loans/api.py::apply_loan()` | Подача заявки на кредит | Source + Sink |
| `apps/loans/api.py::make_decision()` | Изменение статуса заявки менеджером | Source + Sink |
| `apps/audit/service.py::log_action()` | Запись событий в журнал | Sink |
| `core/network.py::get_client_ip()` | Определение IP клиента | Propagation |

### 1.2 Граф вызовов (визуализация)

```mermaid
flowchart TD
    A[HTTP Request] --> B[Auth/Loans/Audit API]
    B --> C[JWTAuth.authenticate]
    C --> D[core.security.decode_token]
    D --> E[auth_app.services.is_token_revoked]

    B --> F[auth_app.api.login]
    F --> G[auth_app.services.is_login_blocked]
    F --> H[core.security.verify_password]
    F --> I[core.security.create_access_token]
    F --> J[core.security.create_refresh_token]

    B --> K[auth_app.api.refresh_tokens]
    K --> D
    K --> L[auth_app.services.revoke_token]
    K --> I
    K --> J

    B --> M[loans.api.make_decision]
    M --> N[loans._get_loan_or_404(select_for_update)]
    M --> O[audit.service.log_action]

    B --> P[loans.api.apply_loan]
    P --> O
```

### 1.3 Анализ потоков данных (SQLi / Command Injection / Path Traversal / XSS)

1. **SQL Injection**  
Source: поля `email`, `amount`, `purpose`, `comment` из HTTP-запросов.  
Propagation: схемы `pydantic` + ORM-фильтры/создание.  
Sink: `User.objects.filter/create`, `CreditApplication.objects.create/get`.  
Вывод: прямого SQL-конкатенирования нет, риск SQLi в текущем коде низкий.

2. **Command Injection**  
Source: пользовательский ввод API.  
Sink: вызовы ОС (`subprocess/os.system`) в runtime-коде отсутствуют.  
Вывод: прямого sink нет, но риск возникнет при добавлении shell-команд без безопасной обвязки.

3. **Path Traversal**  
Source: пользовательские пути файлов в API отсутствуют.  
Sink: операции `open()/FileResponse` по пользовательскому пути отсутствуют.  
Вывод: прямой path traversal в текущем MVP не выявлен.

4. **XSS**  
Source: `purpose`, `comment`, `full_name`.  
Propagation: данные сохраняются в БД и могут возвращаться клиентам в JSON.  
Sink: потенциальный фронтенд-рендер без экранирования.  
Вывод: сервер дополнительно режет HTML-подобный ввод (`<`/`>`), что снижает риск stored XSS.

### 1.4 Анализ зависимостей управления

Проверено, выполняются ли критические действия только под корректными условиями:

1. Проверка ролей перед `make_decision` и `audit/logs` есть.
2. Перед refresh/logout есть проверка структуры и типа токена.
3. До исправлений отсутствовала атомарность для двух чувствительных операций (refresh/decision), что позволяло race-condition.
4. После исправлений критические ветки заключены в транзакции и блокировки строк.

### 1.5 Анализ модульных и библиотечных зависимостей

Критичные по безопасности узлы:

1. `core/security.py` — JWT и пароли.
2. `apps/auth_app/services.py` — анти-bruteforce и denylist токенов.
3. `apps/loans/api.py` — бизнес-критичные решения по заявкам.
4. `config/settings.py` — режим безопасности рантайма.
5. Зависимости: `django`, `PyJWT`, `bcrypt`, `django-ninja`, `psycopg2-binary`.

### 1.6 Выявленные потенциальные уязвимости (не менее 8)

| № | Файл | Тип проблемы | Source | Sink | Последствие | Критичность | Статус |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `apps/auth_app/api.py` + `apps/loans/api.py` | Доверие к spoofed `X-Forwarded-For` | HTTP header | Логи/лимитер | Обход лимитов, подмена IP в аудите | Высокая | Исправлено |
| 2 | `apps/auth_app/services.py` | Brute-force bypass через распределённые IP | login input | throttle lookup | Подбор пароля с ротацией IP | Высокая | Исправлено |
| 3 | `apps/auth_app/api.py::refresh_tokens` | Refresh replay race | refresh token | выдача новых токенов | Повторная эмиссия токенов | Критическая | Исправлено |
| 4 | `apps/loans/api.py::make_decision` | Race condition при принятии решения | decision request | запись статуса заявки | Неконсистентные решения | Высокая | Исправлено |
| 5 | `apps/loans/api.py::list_loans` | Отсутствие пагинации | list request | возврат полного queryset | Memory/DoS риск | Высокая | Исправлено |
| 6 | `core/security.py::decode_token` | Неполная валидация claims JWT | token payload | auth context | Token confusion при reuse секрета | Высокая | Исправлено |
| 7 | `config/settings.py` | Неполные prod-security настройки | deployment config | HTTP transport | MitM/clickjacking/CSRF-риски | Высокая | Исправлено |
| 8 | `setup_db.sql` | Hardcoded пароль в инфраструктурном скрипте | repo content | DB credential creation | Утечка учётных данных БД | Высокая | Исправлено |

### 1.7 Статистический анализ ручной проверки

#### Распределение по типам

| Тип проблемы | Количество | Доля |
| --- | --- | --- |
| Аутентификация / токены | 3 | 37.5% |
| Контроль доступа / целостность бизнес-операций | 2 | 25.0% |
| Конфигурация и инфраструктура | 2 | 25.0% |
| Доступность (DoS) | 1 | 12.5% |

#### Распределение по критичности

| Критичность | Количество |
| --- | --- |
| Критическая | 1 |
| Высокая | 7 |
| Средняя | 0 |
| Низкая | 0 |

Вывод: наибольший риск был связан с токенами/аутентификацией и транзакционной целостностью критичных операций.

---

## Задание 2. Автоматическое выявление проблем

### 2.1 Инструменты и команды

Использованы:

1. `bandit` — SAST для Python-кода.
2. `pip-audit` — SCA для Python-зависимостей.
3. `python manage.py check --deploy` — security-check конфигурации Django.

Команды:

```bash
.venv/bin/bandit -r apps core config -x "*/tests.py" -q
XDG_CACHE_HOME=/tmp/pip-audit-cache .venv/bin/pip-audit -r requirements.txt --no-deps --disable-pip
.venv/bin/python manage.py check --deploy
```

### 2.2 Автоматический анализ текущего MVP

Итог запуска:

1. `bandit`: 0 проблем (`reports/bandit.txt`).
2. `pip-audit`: 0 известных CVE в pinned `requirements.txt` (`reports/pip-audit.txt`).
3. `django check --deploy`: 0 предупреждений (`reports/django-check-deploy.txt`).

### 2.3 Исправленные критичные проблемы (>=5)

Ниже показаны «до/после» (небезопасный и исправленный вариант).

#### Fix 1: Refresh replay race

```python
# Было (уязвимо к race):
# revoke_token(payload=payload, user=user, reason="refresh_rotated")
# access = create_access_token(...)
# refresh = create_refresh_token(...)

# Стало:
with transaction.atomic():
    if not revoke_token(payload=payload, user=user, reason="refresh_rotated"):
        raise HttpError(401, "Invalid token")
    access = create_access_token(user.pk, user.role)
    refresh = create_refresh_token(user.pk)
```

#### Fix 2: Rate limit bypass

```python
# Было: только один scope email|ip
# _scope_key(email, ip)

# Стало: двойной scope (email + email|ip)
return [
    (f"email:{normalized_email}", None),
    (f"email_ip:{normalized_email}|{ip_address or 'unknown'}", ip_address),
]
```

#### Fix 3: Loan decision race

```python
# Было: чтение + запись без блокировки строки
# loan = _get_loan_or_404(loan_id)

# Стало: транзакция + select_for_update
with transaction.atomic():
    loan = _get_loan_or_404(loan_id, for_update=True)
    ...
```

#### Fix 4: Spoofed client IP

```python
# Было: безусловное доверие X-Forwarded-For
# forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

# Стало: доверие proxy-заголовкам только при включённом флаге
if getattr(settings, "TRUST_PROXY_HEADERS", False):
    forwarded_ip = _extract_forwarded_ip(...)
```

#### Fix 5: Неполная JWT валидация

```python
# Было: jwt.decode(token, secret, algorithms=["HS256"])

# Стало:
jwt.decode(
    token,
    _jwt_secret(),
    algorithms=["HS256"],
    audience=JWT_AUDIENCE,
    issuer=JWT_ISSUER,
    options={"require": ["sub", "iss", "aud", "iat", "exp", "type", "jti"]},
)
```

#### Дополнительные исправления

1. Включены `CsrfViewMiddleware` и `XFrameOptionsMiddleware`, HTTPS/HSTS/cookie hardening в `config/settings.py`.
2. Добавлена пагинация `page/page_size` в `GET /api/loans/`.
3. Убрано жёсткое хранение пароля БД из `setup_db.sql` (переменная `app_password`).

### 2.4 Сравнение результатов до/после

| Инструмент | До исправлений | После исправлений | Снижение |
| --- | --- | --- | --- |
| `pip-audit` (по `reports/pip-audit-before-fix.txt`) | 13 уязвимостей (`django`:12, `PyJWT`:1) | 0 | 100% |
| `django check --deploy` | 3 security warning | 0 | 100% |
| `bandit` (целевой runtime-код) | 0 high/medium | 0 high/medium | 0% |

---

## Выводы

1. Наиболее полезными в проекте оказались: `pip-audit` (зависимости), `check --deploy` (конфигурация), `bandit` (быстрый SAST-контроль).
2. Автоинструменты не покрывают все логические риски (например, race-condition в бизнес-операциях); такие дефекты выявлены именно ручным анализом.
3. После исправлений закрыты критичные векторы по refresh replay, brute-force bypass, spoofed IP, целостности решения по заявке и security-конфигурации.
4. Для дальнейшего усиления: добавить lockfile с hash-пинами зависимостей и периодический scheduled SAST/SCA в CI.
