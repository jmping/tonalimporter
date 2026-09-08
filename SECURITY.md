# Security Policy

## Project status

ToneGet for Home Assistant is an unofficial community project. It is not affiliated with, endorsed by, or supported by Tonal Systems, Inc.

## Credential handling

The Home Assistant companion flow is designed so your Tonal password is not stored in Git, Docker Compose, Home Assistant YAML, or the Home Assistant config entry.

When authentication is required:

1. Home Assistant presents a native email/password form.
2. Home Assistant sends those credentials over the private local connection to the companion service.
3. The companion service sends the credentials to Tonal's Auth0 endpoint over HTTPS for the authentication exchange.
4. The password is not written to disk by this project.
5. Returned Tonal token material is persisted in the companion service data volume so future syncs can run without storing/re-entering the password.

Treat the token file as sensitive. The service writes it with restrictive permissions (`0600`).

The original standalone `sync_workouts.py` exporter uses credentials interactively and does not require the companion service token persistence model.

## Network exposure

The companion HTTP API has no independent user-authentication layer because it is intended only for a trusted local/private network.

**Do not expose port 8787 to the public internet.** Prefer one of:

- a private Docker network shared with Home Assistant;
- localhost/host-only access where appropriate;
- a trusted LAN or private overlay such as Tailscale when deliberately configured.

Do not place the companion API behind a public reverse proxy unless you add an appropriate authentication and authorization layer yourself.

## Sensitive endpoints

`POST /auth` accepts a Tonal email/password for the one-time authentication exchange. Anyone who can reach this endpoint can submit credentials to the service. This is why the service must remain private.

`GET /summary` exposes personal workout/fitness information. Treat it as private data even though it does not contain the Tonal password or stored token.

The service must never include stored token material in `/health`, `/summary`, logs, or exceptions returned to Home Assistant.

## Privacy

This project includes no analytics, telemetry, tracking pixel, developer cloud relay, or hosted backend.

Your workout data is retrieved from Tonal and processed locally by the companion service/Home Assistant. Exported workout files and Home Assistant history may contain sensitive personal fitness information; protect backups accordingly.

## Reporting a vulnerability

Please do **not** publish passwords, tokens, raw workout exports, or exploit details in a public issue.

For a security-sensitive report, contact the repository maintainer privately through the contact method listed on the maintainer's GitHub profile. Include a concise description, affected version/commit, reproduction steps, and impact. Do not include real credentials.

## User security checklist

- Keep the companion service private.
- Use a strong unique Tonal password.
- Keep Home Assistant and Docker patched.
- Protect the companion data volume and Home Assistant backups.
- Do not paste token files or raw exports into GitHub issues.
- Review configuration changes that alter the `ports:` mapping before deploying them.

## Dependencies

The companion/exporter intentionally keeps its Python dependency set small. Review `requirements.txt` and the Home Assistant custom component manifest before installation.
