$ErrorActionPreference = "Stop"

python .\scripts\generate_dev_cert.py
Write-Output "Generated .certs/dev-cert.pem and .certs/dev-key.pem"
