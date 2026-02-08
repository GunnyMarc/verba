#!/usr/bin/env python3
"""Entry point — launches the Verba web application via Uvicorn over HTTPS."""

import datetime
import ipaddress
import os
from pathlib import Path

import uvicorn
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

WEB_DIR = Path(__file__).resolve().parent
CERTS_DIR = WEB_DIR / "certs"
CERT_FILE = CERTS_DIR / "cert.pem"
KEY_FILE = CERTS_DIR / "key.pem"


def _generate_self_signed_cert():
    """Generate a self-signed TLS certificate and private key."""
    CERTS_DIR.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    KEY_FILE.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    os.chmod(KEY_FILE, 0o600)

    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Generated self-signed certificate in {CERTS_DIR}")


def main():
    # Write PID file
    pid_file = WEB_DIR / ".verba.pid"
    pid_file.write_text(str(os.getpid()))

    # Generate a self-signed certificate if none exists
    if not (CERT_FILE.exists() and KEY_FILE.exists()):
        _generate_self_signed_cert()

    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=30319,
        reload=True,
        ssl_certfile=str(CERT_FILE),
        ssl_keyfile=str(KEY_FILE),
    )


if __name__ == "__main__":
    main()
