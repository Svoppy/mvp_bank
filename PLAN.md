# Практическая работа №3 — Вариант 1: Банковский кредит
# Детальный пошаговый план реализации MVP

## Технологический стек

| Компонент | Технология |
|---|---|
| Web-фреймворк | Django 5.x + **Django Ninja** |
| БД | PostgreSQL |
| ORM | Django ORM (встроенный) |
| Валидация | Pydantic v2 (встроен в Django Ninja) |
| Аутентификация | PyJWT + passlib[bcrypt] |
| Безопасность | pip-audit, bandit |

---

## Структура проекта

```
mvp_bank/
├── .env                        # секреты (не в git)
├── .env.example
├── requirements.txt
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── urls.py                 # подключение Django Ninja router
├── apps/
│   ├── auth_app/               # регистрация, логин, JWT
│   │   ├── models.py           # CustomUser
│   │   ├── schemas.py          # Pydantic схемы
│   │   ├── api.py              # router endpoints
│   │   └── services.py        # бизнес-логика
│   ├── loans/                  # заявки на кредит
│   │   ├── models.py           # CreditApplication
│   │   ├── schemas.py
│   │   ├── api.py
│   │   └── services.py
│   └── audit/                  # журналирование
│       ├── models.py           # AuditLog
│       ├── schemas.py
│       └── api.py
└── core/
    ├── __init__.py
    ├── security.py             # bcrypt + JWT helpers
    ├── auth_backend.py         # Django Ninja HttpBearer
    └── permissions.py          # проверки ролей
```

---

## Сущности БД (минимум 3)

| Сущность | Ключевые поля |
|---|---|
| **User** | id, email, hashed_password, role (CLIENT/MANAGER/ADMIN), full_name, is_active |
| **CreditApplication** | id, client_id(FK→User), amount, term_months, purpose, status (PENDING/APPROVED/REJECTED), manager_id(FK→User nullable), decision_comment, created_at |
| **AuditLog** | id, user_id(FK→User nullable), action, entity_type, entity_id, ip_address, timestamp, details(JSONField) |

---

## API-эндпоинты (7)

| # | Метод | URL | Роль | Описание |
|---|---|---|---|---|
| 1 | POST | `/api/auth/register` | — | Регистрация клиента |
| 2 | POST | `/api/auth/login` | — | Получить JWT токен |
| 3 | POST | `/api/loans/apply` | CLIENT | Подать заявку |
| 4 | GET | `/api/loans/{id}` | CLIENT/MANAGER | Статус заявки (object-level auth) |
| 5 | GET | `/api/loans/` | CLIENT/MANAGER | Список заявок (своих / всех) |
| 6 | PATCH | `/api/loans/{id}/decision` | MANAGER | Одобрить/отклонить |
| 7 | GET | `/api/audit/logs` | ADMIN | Журнал действий |

---

## Пошаговая реализация

---

### Шаг 1 — Окружение и зависимости

**1.1** Создать виртуальное окружение и установить зависимости:

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install django django-ninja psycopg2-binary python-dotenv \
            passlib[bcrypt] PyJWT pydantic[email] \
            pip-audit bandit
pip freeze > requirements.txt
```

**1.2** Создать файл `.env`:

```
SECRET_KEY=замени-на-случайную-строку-50-символов
DB_NAME=mvp_bank
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET=замени-на-другую-случайную-строку
JWT_ACCESS_TTL_MINUTES=30
JWT_REFRESH_TTL_DAYS=7
```

**1.3** Создать `.env.example` — копия `.env` но без реальных значений (пустые строки).

**1.4** Добавить в `.gitignore`:
```
.env
__pycache__/
*.pyc
venv/
```

---

### Шаг 2 — Django проект и настройки

**2.1** Создать проект:

```bash
django-admin startproject config .
python manage.py startapp auth_app apps/auth_app
python manage.py startapp loans apps/loans
python manage.py startapp audit apps/audit
```

**2.2** Настроить `config/settings.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'apps.auth_app',
    'apps.loans',
    'apps.audit',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

AUTH_USER_MODEL = 'auth_app.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

**2.3** Настроить `config/urls.py`:

```python
from django.urls import path
from .api import api

urlpatterns = [
    path('api/', api.urls),
]
```

**2.4** Создать `config/api.py` — главный NinjaAPI:

```python
from ninja import NinjaAPI
from apps.auth_app.api import router as auth_router
from apps.loans.api import router as loans_router
from apps.audit.api import router as audit_router

api = NinjaAPI(title='Bank Credit MVP', version='1.0')
api.add_router('/auth', auth_router)
api.add_router('/loans', loans_router)
api.add_router('/audit', audit_router)
```

---

### Шаг 3 — Модели Django ORM

**3.1** `apps/auth_app/models.py` — модель пользователя:

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserRole(models.TextChoices):
    CLIENT = 'CLIENT'
    MANAGER = 'MANAGER'
    ADMIN = 'ADMIN'

class UserManager(BaseUserManager):
    def create_user(self, email, password, full_name, role=UserRole.CLIENT):
        user = self.model(email=self.normalize_email(email),
                          full_name=full_name, role=role)
        user.hashed_password = password   # уже хешированный
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    hashed_password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=UserRole.choices,
                            default=UserRole.CLIENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # AbstractBaseUser требует password — переопределяем, не используем
    password = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    class Meta:
        db_table = 'users'
```

**3.2** `apps/loans/models.py` — кредитная заявка:

```python
from django.db import models
from apps.auth_app.models import User

class ApplicationStatus(models.TextChoices):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'

class CreditApplication(models.Model):
    client = models.ForeignKey(User, on_delete=models.PROTECT,
                               related_name='applications')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term_months = models.IntegerField()
    purpose = models.CharField(max_length=500)
    status = models.CharField(max_length=10,
                               choices=ApplicationStatus.choices,
                               default=ApplicationStatus.PENDING)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='managed_applications')
    decision_comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'credit_applications'
```

**3.3** `apps/audit/models.py` — журнал:

```python
from django.db import models
from apps.auth_app.models import User

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL,
                             null=True, blank=True)
    action = models.CharField(max_length=100)    # LOGIN, REGISTER, APPLY, DECISION, UNAUTHORIZED
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    class Meta:
        db_table = 'audit_logs'
```

**3.4** Создать и применить миграции:

```bash
python manage.py makemigrations auth_app loans audit
python manage.py migrate
```

---

### Шаг 4 — core/security.py (bcrypt + JWT)

**4.1** `core/security.py`:

```python
import os
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto',
                           bcrypt__rounds=12)

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = 'HS256'
ACCESS_TTL = int(os.environ.get('JWT_ACCESS_TTL_MINUTES', 30))
REFRESH_TTL = int(os.environ.get('JWT_REFRESH_TTL_DAYS', 7))


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TTL)
    return jwt.encode({'sub': str(user_id), 'role': role,
                       'exp': exp, 'type': 'access'},
                      JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
```

**4.2** `core/auth_backend.py` — Django Ninja Bearer аутентификация:

```python
from ninja.security import HttpBearer
from ninja.errors import HttpError
from core.security import decode_token
from apps.auth_app.models import User
import jwt


class JWTAuth(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            raise HttpError(401, 'Token expired')
        except jwt.InvalidTokenError:
            raise HttpError(401, 'Invalid token')

        user = User.objects.filter(pk=payload['sub'],
                                   is_active=True).first()
        if not user:
            raise HttpError(401, 'User not found')
        return user
```

**4.3** `core/permissions.py` — декораторы проверки ролей:

```python
from ninja.errors import HttpError


def require_role(*roles):
    """Использовать внутри endpoint-а: require_role('MANAGER')(request.auth)"""
    def check(user):
        if user.role not in roles:
            raise HttpError(403, 'Forbidden')
    return check
```

---

### Шаг 5 — apps/auth_app/ (регистрация и логин)

**5.1** `apps/auth_app/schemas.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True
```

**5.2** `apps/auth_app/services.py`:

```python
from apps.auth_app.models import User
from core.security import hash_password, verify_password, create_access_token
from apps.audit.services import log_action
from ninja.errors import HttpError


def register_user(data, ip: str) -> User:
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, 'Email already registered')
    user = User.objects.create_user(
        email=data.email,
        password=hash_password(data.password),
        full_name=data.full_name,
    )
    log_action(user=user, action='REGISTER', ip=ip)
    return user


def login_user(data, ip: str) -> str:
    user = User.objects.filter(email=data.email, is_active=True).first()
    if not user or not verify_password(data.password, user.hashed_password):
        log_action(user=None, action='LOGIN_FAILED', ip=ip,
                   details={'email': data.email})
        raise HttpError(401, 'Invalid credentials')
    log_action(user=user, action='LOGIN', ip=ip)
    return create_access_token(user.id, user.role)
```

**5.3** `apps/auth_app/api.py`:

```python
from ninja import Router
from .schemas import RegisterIn, LoginIn, TokenOut, UserOut
from .services import register_user, login_user
from core.auth_backend import JWTAuth

router = Router(tags=['Auth'])


@router.post('/register', response=UserOut)
def register(request, data: RegisterIn):
    ip = request.META.get('REMOTE_ADDR')
    user = register_user(data, ip)
    return user


@router.post('/login', response=TokenOut, auth=None)
def login(request, data: LoginIn):
    ip = request.META.get('REMOTE_ADDR')
    token = login_user(data, ip)
    return {'access_token': token}
```

---

### Шаг 6 — apps/loans/ (заявки)

**6.1** `apps/loans/schemas.py`:

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional


class LoanApplyIn(BaseModel):
    amount: Decimal = Field(gt=0, le=50_000_000)
    term_months: int = Field(ge=1, le=360)
    purpose: str = Field(max_length=500)


class DecisionIn(BaseModel):
    status: str = Field(pattern='^(APPROVED|REJECTED)$')
    decision_comment: str = Field(default='', max_length=1000)


class LoanOut(BaseModel):
    id: int
    amount: Decimal
    term_months: int
    purpose: str
    status: str
    decision_comment: str
    created_at: datetime
    client_id: int
    manager_id: Optional[int]

    class Config:
        from_attributes = True
```

**6.2** `apps/loans/services.py`:

```python
from apps.loans.models import CreditApplication, ApplicationStatus
from apps.audit.services import log_action
from ninja.errors import HttpError


def apply_for_loan(client, data, ip: str) -> CreditApplication:
    app = CreditApplication.objects.create(
        client=client,
        amount=data.amount,
        term_months=data.term_months,
        purpose=data.purpose,
    )
    log_action(user=client, action='APPLY', entity_type='CreditApplication',
               entity_id=app.id, ip=ip)
    return app


def get_application(app_id: int, user) -> CreditApplication:
    app = CreditApplication.objects.filter(pk=app_id).first()
    if not app:
        raise HttpError(404, 'Not found')
    # object-level auth
    if user.role == 'CLIENT' and app.client_id != user.id:
        log_action(user=user, action='UNAUTHORIZED', entity_type='CreditApplication',
                   entity_id=app_id)
        raise HttpError(403, 'Forbidden')
    return app


def list_applications(user):
    if user.role == 'CLIENT':
        return CreditApplication.objects.filter(client=user)
    return CreditApplication.objects.all()


def make_decision(app_id: int, manager, data, ip: str) -> CreditApplication:
    app = CreditApplication.objects.filter(pk=app_id).first()
    if not app:
        raise HttpError(404, 'Not found')
    if app.status != ApplicationStatus.PENDING:
        raise HttpError(400, 'Already decided')
    app.status = data.status
    app.decision_comment = data.decision_comment
    app.manager = manager
    app.save()
    log_action(user=manager, action='DECISION', entity_type='CreditApplication',
               entity_id=app.id, ip=ip,
               details={'status': data.status})
    return app
```

**6.3** `apps/loans/api.py`:

```python
from ninja import Router
from typing import List
from .schemas import LoanApplyIn, DecisionIn, LoanOut
from .services import apply_for_loan, get_application, list_applications, make_decision
from core.auth_backend import JWTAuth
from core.permissions import require_role

router = Router(tags=['Loans'], auth=JWTAuth())


@router.post('/apply', response=LoanOut)
def apply(request, data: LoanApplyIn):
    require_role('CLIENT')(request.auth)
    ip = request.META.get('REMOTE_ADDR')
    return apply_for_loan(request.auth, data, ip)


@router.get('/', response=List[LoanOut])
def list_loans(request):
    require_role('CLIENT', 'MANAGER')(request.auth)
    return list(list_applications(request.auth))


@router.get('/{app_id}', response=LoanOut)
def get_loan(request, app_id: int):
    require_role('CLIENT', 'MANAGER')(request.auth)
    return get_application(app_id, request.auth)


@router.patch('/{app_id}/decision', response=LoanOut)
def decision(request, app_id: int, data: DecisionIn):
    require_role('MANAGER')(request.auth)
    ip = request.META.get('REMOTE_ADDR')
    return make_decision(app_id, request.auth, data, ip)
```

---

### Шаг 7 — apps/audit/ (журнал)

**7.1** `apps/audit/services.py`:

```python
from apps.audit.models import AuditLog


def log_action(user=None, action='', entity_type='', entity_id=None,
               ip=None, details=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip,
        details=details or {},
    )
```

**7.2** `apps/audit/schemas.py`:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[int]
    ip_address: Optional[str]
    timestamp: datetime
    details: dict

    class Config:
        from_attributes = True
```

**7.3** `apps/audit/api.py`:

```python
from ninja import Router
from typing import List
from .schemas import AuditLogOut
from .models import AuditLog
from core.auth_backend import JWTAuth
from core.permissions import require_role

router = Router(tags=['Audit'], auth=JWTAuth())


@router.get('/logs', response=List[AuditLogOut])
def audit_logs(request):
    require_role('ADMIN')(request.auth)
    return list(AuditLog.objects.order_by('-timestamp')[:500])
```

---

### Шаг 8 — Тестовые данные (seeder)

Создать `seeder.py` в корне проекта:

```python
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.auth_app.models import User
from apps.loans.models import CreditApplication
from core.security import hash_password

# Пользователи
client = User.objects.create_user(
    email='client@example.com',
    password=hash_password('Password123!'),
    full_name='Иван Клиентов',
    role='CLIENT',
)
manager = User.objects.create_user(
    email='manager@example.com',
    password=hash_password('Password123!'),
    full_name='Мария Менеджерова',
    role='MANAGER',
)
admin = User.objects.create_user(
    email='admin@example.com',
    password=hash_password('Password123!'),
    full_name='Александр Администратов',
    role='ADMIN',
)

# Заявки
CreditApplication.objects.create(
    client=client, amount=500000, term_months=24, purpose='Покупка автомобиля'
)
CreditApplication.objects.create(
    client=client, amount=1500000, term_months=60, purpose='Ипотека'
)
print('Seeder done.')
```

Запустить:
```bash
python seeder.py
```

---

### Шаг 9 — Проверка безопасности

**9.1** pip-audit:
```bash
pip-audit -r requirements.txt -f json -o audit_report.json
```
Исправить все critical/high CVE (обновить версии в requirements.txt).

**9.2** bandit:
```bash
bandit -r apps/ core/ config/ -f txt -o bandit_report.txt
```
Исправить все HIGH severity находки.

**9.3** Вручную проверить:
- Нет MD5/SHA-1 (только bcrypt)
- Нет секретов в коде
- Токены не попадают в AuditLog.details
- Ошибка логина возвращает всегда "Invalid credentials" (без уточнения — "email not found" запрещено)

---

### Шаг 10 — Запуск и ручное тестирование

```bash
python manage.py runserver
```

Открыть Swagger UI (встроен в Django Ninja):
```
http://localhost:8000/api/docs
```

Проверить каждый эндпоинт через Swagger:
1. `POST /api/auth/register` — зарегистрировать клиента
2. `POST /api/auth/login` — получить токен (скопировать)
3. Нажать **Authorize** в Swagger → вставить токен
4. `POST /api/loans/apply` — подать заявку
5. `GET /api/loans/` — проверить список
6. Залогиниться как MANAGER → `PATCH /api/loans/{id}/decision`
7. Залогиниться как ADMIN → `GET /api/audit/logs`

---

## Чеклист безопасности (Задание 2)

| # | Пункт | Где реализовано |
|---|---|---|
| 1 | Входные данные валидируются Pydantic | schemas.py во всех apps |
| 2 | bcrypt cost=12, нет MD5/SHA-1 | core/security.py |
| 3 | JWT access TTL=30 мин | core/security.py |
| 4 | Нейтральные ошибки ("Invalid credentials") | auth_app/services.py |
| 5 | Серверная проверка ролей | core/permissions.py |
| 6 | Object-level авторизация | loans/services.py::get_application |
| 7 | Нет паролей/токенов в логах | audit/services.py — details не содержат sensitive данных |
| 8 | Секреты только в .env | config/settings.py |
| 9 | .env в .gitignore | .gitignore |
| 10 | pip-audit без critical CVE | audit_report.json |
| 11 | bandit без HIGH | bandit_report.txt |

---

## Таблица находок (Задание 1, пункт 7)

| Уязвимость | Где | Исправление |
|---|---|---|
| Хранение пароля в открытом виде | (не допущено) | bcrypt hash в create_user |
| Информативная ошибка при логине | auth_app/services.py | Всегда "Invalid credentials" |
| Нет проверки владельца заявки | loans/services.py | client_id == user.id проверяется |
| Секрет JWT захардкожен | (не допущено) | Только через os.environ |
| SQL injection | (не допущено) | Только Django ORM |

---

## Порядок сдачи

1. Запустить `pip-audit` и `bandit`, сохранить отчёты
2. Скриншоты каждого эндпоинта в Swagger
3. Написать отчёт по 8 пунктам Задания 1 и 6 чеклистам Задания 2
4. Приложить `requirements.txt`, `.env.example`, `bandit_report.txt`, `audit_report.json`
