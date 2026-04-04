# Практическая работа №3 — Вариант 1: Банковский кредит
# Детальный план реализации MVP

## Бизнес-сценарий
Клиент подаёт заявку на кредит → менеджер банка одобряет/отклоняет → клиент видит статус.

---

## Структура проекта

```
mvp3/
├── .env                    # секреты (не в git)
├── .env.example
├── requirements.txt        # зафиксированные версии
├── manage.py
├── config/
│   ├── settings.py
│   └── urls.py
├── apps/
│   ├── auth/               # регистрация, логин, JWT
│   ├── loans/              # заявки на кредит
│   └── audit/              # журналирование
└── core/
    ├── security.py         # bcrypt, JWT helpers
    ├── permissions.py      # проверка ролей и объектов
    └── middleware.py
```

---

## Сущности БД (минимум 3)

| Сущность | Ключевые поля |
|---|---|
| **User** | id, email, hashed_password, role (CLIENT/MANAGER/ADMIN), full_name, is_active |
| **CreditApplication** | id, client_id(FK), amount, term_months, purpose, status (PENDING/APPROVED/REJECTED), manager_id(FK), decision_comment |
| **AuditLog** | id, user_id(FK), action, entity_type, entity_id, ip_address, timestamp, details(JSON) |

---

## API-эндпоинты (5+)

| # | Метод | URL | Роль | Описание |
|---|---|---|---|---|
| 1 | POST | `/auth/register` | — | Регистрация клиента |
| 2 | POST | `/auth/login` | — | JWT токен |
| 3 | POST | `/loans/apply` | CLIENT | Подать заявку |
| 4 | GET | `/loans/{id}` | CLIENT/MANAGER | Статус заявки (object-level auth) |
| 5 | GET | `/loans/` | CLIENT/MANAGER | Список заявок (своих / всех) |
| 6 | PATCH | `/loans/{id}/decision` | MANAGER | Одобрить/отклонить |
| 7 | GET | `/audit/logs` | ADMIN | Журнал действий |

---

## Меры безопасности

### Аутентификация
- `passlib[bcrypt]` — хеш паролей (cost factor >= 12)
- `PyJWT` — access token (TTL 30 мин), refresh token (7 дней)
- Нейтральные сообщения об ошибках ("invalid credentials")

### Авторизация
- Ролевая: CLIENT / MANAGER / ADMIN
- Объектная: `GET /loans/{id}` проверяет `application.client_id == current_user.id` ИЛИ роль MANAGER
- Все проверки — на сервере

### Валидация (Pydantic)
- Сумма: `amount: Decimal = Field(gt=0, le=50_000_000)`
- Срок: `term_months: int = Field(ge=1, le=360)`
- Email: `EmailStr`
- Пароль: минимум 8 символов
- Цель: `max_length=500`

### Логирование
- AuditLog при: логин, регистрация, подача заявки, решение, неавторизованный доступ
- Никаких паролей/токенов в логах

### Криптография
- bcrypt (cost factor >= 12), нет MD5/SHA-1
- Секреты только в `.env`, `.env` в `.gitignore`

### Зависимости
- `pip-audit` → исправить critical/high CVE
- `bandit -r . -f txt` → исправить B-rated

---

## Отчёт — Задание 1 (8 пунктов)

1. **Область анализа** — модули auth, loans, audit; 7 эндпоинтов; зависимости
2. **Контекст** — активы: ПД клиентов, финансовые данные; роли; границы доверия
3. **Структурная схема + блок-схема** сценария подачи и одобрения заявки
4. **Критичные участки** — `POST /auth/login`, `PATCH /loans/{id}/decision`, AuditLog
5. **Анализ потока данных** — `login(email, password)` → Pydantic → bcrypt.verify → JWT → response
6. **Проверка механизмов** — аутентификация, авторизация, валидация, логирование, ошибки, крипто
7. **Таблица находок** — уязвимости найденные и исправленные
8. **Рекомендации** — параметризация, вынос секретов, обновление зависимостей

---

## Отчёт — Задание 2 (6 чеклистов)

1. Входные данные (Pydantic validators)
2. Аутентификация (bcrypt, JWT TTL, logout)
3. Авторизация (серверные проверки, object-level)
4. Данные и логирование (нет лишних полей в API, нет паролей в логах)
5. Криптография (bcrypt cost>=12, нет хардкода секретов)
6. Зависимости (pip-audit report, bandit report)

---

## Порядок реализации

1. `requirements.txt` + `.env` + Django проект + PostgreSQL
2. Модели SQLAlchemy (User, CreditApplication, AuditLog)
3. `core/security.py` (bcrypt + JWT helpers)
4. `apps/auth/` (register + login)
5. `apps/loans/` (apply + list + get + decision)
6. `apps/audit/` (log writes + admin view)
7. Тестовые данные (seeder/fixtures)
8. `pip-audit` + `bandit`, исправление
9. Написание отчёта
