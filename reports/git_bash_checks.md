# Git Bash: краткий запуск проверок

```bash
cd /c/projects/aitu/isscv/mvp3/mvp_bank
source .venv/Scripts/activate

export DB_ENGINE=sqlite
export SQLITE_PATH='C:\projects\aitu\isscv\mvp3\mvp_bank\db.sqlite3'
export DEBUG=False

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py check --deploy

PYTHONPATH="$(pwd)/.tools" ./.tools/bin/bandit.exe -r apps core config seed.py -f txt
PYTHONPATH="$(pwd)/.tools" ./.tools/bin/pip-audit.exe -r requirements.txt --progress-spinner off
```

HTTPS Swagger:

```bash
python scripts/generate_dev_cert.py
export DB_ENGINE=sqlite
export SQLITE_PATH='C:\projects\aitu\isscv\mvp3\mvp_bank\db.sqlite3'
.venv/Scripts/python.exe scripts/run_https.py --host 127.0.0.1 --port 7443
```

Открыть:

```text
https://127.0.0.1:7443/api/docs
```
