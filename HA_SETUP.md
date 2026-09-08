# Home Assistant companion service

This branch adds a small local HTTP service that periodically retrieves your Tonal data and exposes a compact JSON summary for Home Assistant.

## Why use a companion service?

Home Assistant only reads a local HTTP endpoint. Tonal credentials stay with the companion container and are not stored in Home Assistant YAML or committed to Git.

## 1. Configure credentials

Create a local `.env` file next to `docker-compose.example.yml` (do not commit it):

```env
TONAL_EMAIL=you@example.com
TONAL_PASSWORD=your-password
TONAL_SYNC_INTERVAL_MINUTES=180
```

The repository `.gitignore` should keep standard `.env` files out of Git; verify before committing local changes.

## 2. Start the service

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up -d --build
```

The example Compose file binds the service to `127.0.0.1:8787` on the Docker host.

Check it locally:

```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/summary
```

Endpoints:

- `/health` — service status, last successful sync, last error
- `/summary` — HA-friendly workout and Strength Score summary

## 3. Make the endpoint reachable from Home Assistant

If Home Assistant runs in Docker on the same host, `127.0.0.1` inside the HA container is the HA container itself, not the Docker host.

On Docker Desktop for macOS, `host.docker.internal` normally resolves to the Docker host. The example `home_assistant/rest.yaml` therefore uses:

```text
http://host.docker.internal:8787/summary
```

If your Home Assistant container cannot reach that address, attach both containers to the same user-defined Docker network and use `http://tonalimporter:8787/summary` instead. In that configuration, remove the localhost-only `ports` binding if you do not need host access.

## 4. Add the Home Assistant sensors

The repository contains `home_assistant/rest.yaml`. Either merge that block into your existing `rest:` configuration or include it from `configuration.yaml`:

```yaml
rest: !include rest.yaml
```

If you already have a `rest:` key, do not add a second one; merge the entries instead.

Run Home Assistant's configuration check before restarting.

## Sensors included

- `sensor.tonal_service_status`
- `sensor.tonal_total_workouts`
- `sensor.tonal_latest_workout`
- `sensor.tonal_workouts_7_days`
- `sensor.tonal_workouts_30_days`
- `sensor.tonal_volume_7_days`
- `sensor.tonal_volume_30_days`
- `sensor.tonal_strength_score`
- `sensor.tonal_upper_strength_score`
- `sensor.tonal_lower_strength_score`
- `sensor.tonal_core_strength_score`

The main Strength Score sensor also carries region and individual-muscle data as attributes.

## Security notes

- Never commit Tonal credentials or the `.env` file.
- Keep the service private to the Docker host or a private Docker network; it has no authentication layer because it is intended only for trusted local access.
- The service polls Tonal every 180 minutes by default to avoid unnecessary unofficial API traffic.
- This project uses an unofficial Tonal API workflow and may stop working if Tonal changes authentication or API behavior.
