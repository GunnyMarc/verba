#!/usr/bin/env python3
"""Entry point — launches the Verba web application via Uvicorn."""

import os
from pathlib import Path

import uvicorn

WEB_DIR = Path(__file__).resolve().parent


def main():
    # Write PID file
    pid_file = WEB_DIR / ".verba.pid"
    pid_file.write_text(str(os.getpid()))

    cert_file = WEB_DIR / "certs" / "cert.pem"
    key_file = WEB_DIR / "certs" / "key.pem"

    ssl_kwargs = {}
    if cert_file.exists() and key_file.exists():
        ssl_kwargs["ssl_certfile"] = str(cert_file)
        ssl_kwargs["ssl_keyfile"] = str(key_file)

    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=30319,
        reload=True,
        **ssl_kwargs,
    )


if __name__ == "__main__":
    main()
