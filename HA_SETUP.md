# Home Assistant companion service

This branch adds a local Tonal data service plus a Home Assistant custom integration with native UI setup and reauthentication.

## Authentication model

Tonal credentials are **not** stored in Docker Compose, Home Assistant YAML, or this repository.

When Tonal authentication is missing or expires, Home Assistant marks the integration as requiring reauthentication. Open the integration in the Home Assistant app and choose **Reconfigure / Reauthenticate**. The native HA form asks for your Tonal email and password; iOS/macOS Password AutoFill can supply those fields. Home Assistant sends the credentials over the private local connection to the companion service, which uses them for the Tonal OAuth exchange and does not persist the password.

The companion service persists only Tonal's returned token material in `/data/tonal_token.json`, with restrictive file permissions. If Tonal stops accepting that token, the service returns `auth_required` and HA starts the reauthentication flow again.

## 1. Start the companion service

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up -d --build
```

No `.env` credentials are required. The optional environment setting is the sync interval:

```env
TONAL_SYNC_INTERVAL_MINUTES=180
```

Check the service locally:

```bash
curl http://127.0.0.1:8787/health
```

Before authentication, the expected state is `auth_required`.

## 2. Make the service reachable from Home Assistant

If Home Assistant runs in Docker on the same Mac, `127.0.0.1` inside the HA container refers to the HA container, not the Docker host.

Preferred setup: attach Home Assistant and `tonalimporter` to the same private Docker network and configure the integration with:

```text
http://tonalimporter:8787
```

Alternatively, Docker Desktop for macOS commonly exposes the host as:

```text
http://host.docker.internal:8787
```

Keep port 8787 private. There is no reason to expose the companion service to the public internet, Cloudflare, or public SSH.

## 3. Install the Home Assistant custom integration

Copy:

```text
custom_components/tonal_companion/
```

into your Home Assistant configuration directory as:

```text
/config/custom_components/tonal_companion/
```

Restart Home Assistant after installing the component.

Then in Home Assistant:

1. Go to **Settings > Devices & services > Add Integration**.
2. Search for **Tonal Companion**.
3. Enter the private companion-service URL.
4. Because the new service has no Tonal token yet, HA will request reauthentication.
5. Enter your Tonal email and password in the Home Assistant app. Apple Passwords/AutoFill should be available for the email and password selectors.
6. After successful authentication, HA reloads the integration and creates Tonal sensors.

## Reauthentication behavior

The integration uses Home Assistant's native config-entry reauthentication mechanism. If the coordinator sees `auth_required`, it raises `ConfigEntryAuthFailed`; Home Assistant then surfaces the repair/reauthentication flow in the UI and mobile app.

The password is not written into the HA config entry. The config entry contains only the local companion service URL.

## Sensors included

- Strength Score
- Upper Strength Score
- Lower Strength Score
- Core Strength Score
- Workouts 7d
- Workouts 30d
- Volume 7d
- Volume 30d
- Total Workouts
- Latest Workout (with latest-workout details as attributes)

## Security notes

- No Tonal password in Git, Compose, HA YAML, or persistent service state.
- Keep the companion API reachable only from the HA host/private Docker network.
- The returned Tonal token is sensitive and is stored in the service data volume with mode `0600`.
- The service polls Tonal every 180 minutes by default to reduce unnecessary unofficial API traffic.
- Tonal's API/authentication is unofficial and may change without notice.
