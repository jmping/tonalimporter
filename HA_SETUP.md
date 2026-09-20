# ToneGet for Home Assistant setup

ToneGet for Home Assistant uses two local pieces:

1. a Home Assistant custom integration;
2. a separate ToneGet companion service that performs Tonal authentication, synchronization, and local summary generation.

HACS installs and updates the Home Assistant custom integration only. The companion service remains a separate local Docker service and must be updated independently when companion code changes.

## Authentication model

Tonal credentials are **not** stored in Docker Compose, Home Assistant YAML, Git, or the Home Assistant config entry.

When authentication is needed, Home Assistant presents a native email/password reauthentication form. The credentials are sent over the private local connection to the companion service, used for the Tonal/Auth0 authentication exchange, and are not persisted by this project.

The companion stores returned token material in `/data/tonal_token.json` with restrictive permissions. When a refresh token is available, the companion uses it to renew authentication automatically before asking for the password again.

Transient authentication failures do not immediately discard saved token material. The companion keeps retrying periodic syncs, tracks consecutive auth failures, and only marks reauthentication required after the configured threshold is reached. If saved credentials begin working again, a successful sync clears the auth-failure state automatically.

The password itself is not written to disk.

## 1. Start the companion service

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up -d --build
```

No Tonal password is stored in the Compose file.

Optional environment settings include:

```env
TONAL_SYNC_INTERVAL_MINUTES=180
TONAL_AUTH_FAILURE_THRESHOLD=3
```

Check the service locally:

```bash
curl http://127.0.0.1:8787/health
```

Before initial authentication, `auth_required` is expected.

## 2. Make the service reachable from Home Assistant

If Home Assistant runs in Docker, `127.0.0.1` inside the Home Assistant container refers to the Home Assistant container itself, not the Docker host.

Preferred setup: place Home Assistant and `tonalimporter` on the same private Docker network and configure the integration with:

```text
http://tonalimporter:8787
```

Depending on the Docker host, this may also work:

```text
http://host.docker.internal:8787
```

Use the URL that is actually reachable from the Home Assistant container. Do not change a working companion URL unnecessarily.

Keep port 8787 private. Do not expose the companion service directly to the public internet, Cloudflare, or public SSH.

## 3. Install the Home Assistant integration

### HACS

Add this repository to HACS as a custom repository with category **Integration**:

```text
https://github.com/jmping/tonalimporter
```

Install **ToneGet for Home Assistant**, then restart Home Assistant.

### Manual installation

Copy:

```text
custom_components/tonal_companion/
```

to:

```text
/config/custom_components/tonal_companion/
```

and restart Home Assistant.

## 4. Add the integration

1. Go to **Settings > Devices & services > Add Integration**.
2. Search for **ToneGet for Home Assistant**.
3. Enter the private companion-service URL.
4. If authentication is required, Home Assistant will surface its reauthentication flow.
5. Enter the Tonal account email and password in Home Assistant.
6. After successful authentication, Home Assistant reloads the integration and creates sensors.

The config entry stores only the local companion URL, not the Tonal password.

## Reauthentication and recovery

The integration uses Home Assistant's native config-entry reauthentication mechanism.

The companion attempts token refresh and sync recovery before requiring user action. After repeated confirmed authentication failures, it reports `auth_required`; Home Assistant then raises `ConfigEntryAuthFailed` and surfaces a reauthentication prompt.

A reauthentication prompt does not necessarily mean the old token material has been deleted. The companion can continue retrying saved credentials, and a later successful sync clears the failure counter and auth-required state.

## Update behavior

There are two update paths:

- **Home Assistant integration:** update through HACS when a new repository release is available.
- **Companion service:** update the local Git checkout and rebuild/restart the Docker service when companion code changes.

For a Docker Compose deployment:

```bash
git pull --ff-only origin main
docker compose up -d --build
```

Review release notes before upgrading because some releases may change only the HA component while others also change the companion.

## Sensors

Enabled by default:

- Strength Score
- Upper Strength Score
- Lower Strength Score
- Core Strength Score
- Workouts 7d
- Workouts 30d
- Volume 7d
- Volume 30d
- Total Workouts
- Latest Workout

Many additional lifetime, rolling-window, latest-workout, record, strength-region, muscle, recent-workout, and diagnostic entities are created disabled by default.

## Security notes

- Keep the companion API on a trusted private network.
- Treat `/data/tonal_token.json` as sensitive.
- Do not expose port 8787 publicly.
- Protect Home Assistant backups and recorder data because workout information may be sensitive.
- The project uses an unofficial Tonal API/authentication workflow and can break if Tonal changes its service.
