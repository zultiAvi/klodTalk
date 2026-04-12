# Security

## Threat Model

KlodTalk is designed as a **local-network tool**. It is not intended to be exposed to the public internet.

The server supports **WSS (WebSocket Secure)** — TLS-encrypted WebSocket connections using a self-signed certificate. When configured, all traffic between clients and the server is encrypted, protecting passwords and messages from network sniffing. Passwords are additionally SHA-256 hashed on the client before transmission.

**Note:** The self-signed certificate must be manually trusted on each client device. It does not provide the same identity verification as a CA-signed certificate, but it does encrypt all traffic.

If SSL is not configured, the server falls back to plain `ws://` (unencrypted).

## Recommendations

- **Do not expose port 9000 to the internet.** Use a firewall or VPN if you need remote access.
- **Enable WSS** by generating a certificate (`helpers/generate_cert.sh`) and configuring `ssl_cert`/`ssl_key` in `config/server_config.yaml`.
- Run the server only on trusted local networks.
- Use strong, unique passwords for each user account.

## Docker Isolation

Each project runs inside its own Docker container with only its workspace directory mounted. Projects cannot access each other's files or the host filesystem beyond their designated folder and any explicitly configured `allowed_external_paths`.

**External path writability is opt-in.** By default, all external paths are mounted read-only (`ro`). To grant write access, the admin must explicitly set `"writable": true` on individual path entries in `projects.json`. Plain string entries in the legacy format are always read-only.

**Results folders are always writable.** When an external path entry has `"results": true`, it is mounted read-write regardless of the `writable` field. This is by design: the project needs write access to save output files. Admins should ensure the results folder is appropriately scoped.

## Reporting Security Issues

If you discover a security vulnerability, please open a [GitHub issue](../../issues) with the label `security`. For sensitive disclosures, include minimal details in the public issue and we will coordinate privately.
