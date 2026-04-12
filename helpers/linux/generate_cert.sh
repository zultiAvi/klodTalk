#!/usr/bin/env bash
# Generates a self-signed TLS certificate for KlodTalk WSS
set -e

CERT_DIR="${1:-$HOME/.klodtalk/certs}"
mkdir -p "$CERT_DIR"

# Try to auto-detect the LAN IP
DEFAULT_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$DEFAULT_IP" ]; then
    DEFAULT_IP=""
fi

# Prompt for server IP so the cert covers it in SAN
if [ -n "$DEFAULT_IP" ]; then
    read -rp "Server LAN IP address (default: $DEFAULT_IP): " SERVER_IP
    SERVER_IP="${SERVER_IP:-$DEFAULT_IP}"
else
    read -rp "Server LAN IP address (e.g. 192.168.1.100): " SERVER_IP
fi

# Validate — 0.0.0.0 is a bind address, not a real IP for certificate SAN
if [ -z "$SERVER_IP" ] || [ "$SERVER_IP" = "0.0.0.0" ]; then
    echo "Error: A real LAN IP is required (not 0.0.0.0)."
    echo "Clients connect to this IP, so the certificate SAN must match it."
    echo "Hint: check your IP with 'hostname -I' or 'ip addr'"
    exit 1
fi

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout "$CERT_DIR/server.key" \
  -out "$CERT_DIR/server.crt" \
  -subj "/CN=klodtalk" \
  -addext "subjectAltName=IP:$SERVER_IP,IP:127.0.0.1"

echo ""
echo "Certificate generated in $CERT_DIR"
echo "  $CERT_DIR/server.crt  (give this to clients that need to trust it)"
echo "  $CERT_DIR/server.key  (keep private, server-only)"
echo ""
echo "Next steps:"
echo "  1. Set ssl_cert and ssl_key in config/server_config.yaml"
echo "  2. Restart the server"
echo "  3. For web browser: navigate to https://$SERVER_IP:9000 and accept the self-signed cert, then switch to wss:// in the web client"
echo "  4. For Android: copy server.crt to your device using one of these methods:"
echo "       - Email it to yourself and open the attachment"
echo "       - Copy via USB: adb push $CERT_DIR/server.crt /sdcard/Download/"
echo "       - Share via cloud storage (Google Drive, etc.)"
echo "     Then install: Settings > Security > Install a certificate > CA certificate"
echo ""
echo "Note: if your server IP changes, you must regenerate the certificate."
