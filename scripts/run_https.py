from __future__ import annotations

import argparse
import os
import ssl
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402
from scripts.generate_dev_cert import ensure_dev_certificate  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MVP Bank API over HTTPS for local demonstration.")
    parser.add_argument("--host", default=os.environ.get("HTTPS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("HTTPS_PORT", "7443")))
    parser.add_argument("--cert", default=os.environ.get("HTTPS_CERT_FILE", ".certs/dev-cert.pem"))
    parser.add_argument("--key", default=os.environ.get("HTTPS_KEY_FILE", ".certs/dev-key.pem"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cert_path = Path(args.cert).resolve()
    key_path = Path(args.key).resolve()
    if not cert_path.is_file() or not key_path.is_file():
        ensure_dev_certificate(cert_path, key_path, common_name=args.host)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)

    django_app = get_wsgi_application()

    def https_application(environ, start_response):
        environ["wsgi.url_scheme"] = "https"
        environ["HTTPS"] = "on"
        return django_app(environ, start_response)

    httpd = make_server(args.host, args.port, https_application, handler_class=WSGIRequestHandler)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"HTTPS server running at https://{args.host}:{args.port}/api/docs")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
