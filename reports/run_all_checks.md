# Как запускать все тесты и проверки

Рабочая папка:

```powershell
cd C:\projects\aitu\isscv\mvp3\mvp_bank
.\.venv\Scripts\Activate.ps1
```

## 1. Настроить локальный SQLite-режим

```powershell
$env:DB_ENGINE='sqlite'
$env:SQLITE_PATH='C:\projects\aitu\isscv\mvp3\mvp_bank\db.sqlite3'
$env:DEBUG='False'
```

## 2. Проверить миграции

```powershell
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

## 3. Запустить все unit/API tests

```powershell
python manage.py test
```

Ожидаемый результат:

```text
Ran 13 tests
OK
```

## 4. Проверить production-настройки Django

```powershell
python manage.py check --deploy
```

Ожидаемый результат:

```text
System check identified no issues (0 silenced).
```

## 5. Запустить SAST через Bandit

```powershell
$env:PYTHONPATH=(Resolve-Path .\.tools).Path
.\.tools\bin\bandit.exe -r apps core config seed.py -f txt
```

Ожидаемый результат:

```text
No issues identified.
```

## 6. Запустить SCA через pip-audit

```powershell
$env:PYTHONPATH=(Resolve-Path .\.tools).Path
.\.tools\bin\pip-audit.exe -r requirements.txt --progress-spinner off
```

Ожидаемый результат:

```text
No known vulnerabilities found
```

## 7. Записать результаты в reports

```powershell
python manage.py test > reports\pw5-test-results.txt 2>&1
python manage.py check --deploy > reports\pw5-django-check-deploy.txt 2>&1

$env:PYTHONPATH=(Resolve-Path .\.tools).Path
.\.tools\bin\bandit.exe -r apps core config seed.py -f txt > reports\pw5-bandit.txt 2>&1
.\.tools\bin\pip-audit.exe -r requirements.txt --progress-spinner off > reports\pw5-pip-audit.txt 2>&1
```

## 8. Запустить HTTPS Swagger

Если сертификаты ещё не созданы:

```powershell
python scripts\generate_dev_cert.py
```

Запуск HTTPS:

```powershell
$env:DB_ENGINE='sqlite'
$env:SQLITE_PATH='C:\projects\aitu\isscv\mvp3\mvp_bank\db.sqlite3'
.\.venv\Scripts\python.exe scripts\run_https.py --host 127.0.0.1 --port 7443
```

Открыть Swagger:

```text
https://127.0.0.1:7443/api/docs
```

Браузер может показать предупреждение о self-signed сертификате. Для локальной демонстрации это нормально.

## 9. Быстрая проверка HTTPS из PowerShell

```powershell
@'
import ssl, urllib.request
ctx = ssl._create_unverified_context()
with urllib.request.urlopen('https://127.0.0.1:7443/api/docs', context=ctx, timeout=5) as resp:
    print(f'STATUS={resp.status}')
'@ | python -
```

Ожидаемый результат:

```text
STATUS=200
```

## 10. Полный порядок перед сдачей

```powershell
cd C:\projects\aitu\isscv\mvp3\mvp_bank
.\.venv\Scripts\Activate.ps1

$env:DB_ENGINE='sqlite'
$env:SQLITE_PATH='C:\projects\aitu\isscv\mvp3\mvp_bank\db.sqlite3'
$env:DEBUG='False'

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py check --deploy

$env:PYTHONPATH=(Resolve-Path .\.tools).Path
.\.tools\bin\bandit.exe -r apps core config seed.py -f txt
.\.tools\bin\pip-audit.exe -r requirements.txt --progress-spinner off
```
