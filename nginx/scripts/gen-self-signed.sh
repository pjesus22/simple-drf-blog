#!/usr/bin/env sh
# Generates a self-signed TLS certificate valid for 1 year.
# Run this once before the first `docker compose up`:
#
#   chmod +x nginx/scripts/gen-self-signed.sh
#   ./nginx/scripts/gen-self-signed.sh

set -e

CERT_DIR="$(dirname "$0")/../certs/self-signed"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days 365 \
  -subj "/C=US/ST=Local/L=Local/O=Blog/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "Self-signed certificate generated at $CERT_DIR"
echo "To switch to Let's Encrypt, see the comments in nginx/conf.d/blog.conf"
