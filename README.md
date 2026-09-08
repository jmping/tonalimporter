# ToneGet for Home Assistant

<p align="center">
  <img src="handle.jpg" alt="Generic strength-training handle artwork" width="320">
</p>

Unofficial Home Assistant integration and local companion service for accessing your own Tonal workout data.

> **Not affiliated with Tonal Systems, Inc.** This is a community project. It is not produced, endorsed, sponsored, or supported by Tonal Systems, Inc. "Tonal" is used only to identify compatibility with the service. The artwork above is generic strength-training artwork, not Tonal branding.

This repository is a fork of the community **ToneGet** exporter and retains its data-export functionality. This fork adds a local companion service plus a Home Assistant custom integration so workout and Strength Score data can appear as Home Assistant entities.

## What it does

- Authenticates to Tonal using the same unofficial API workflow used by ToneGet.
- Keeps your Tonal password out of Git, Docker Compose, and Home Assistant YAML.
- Lets Home Assistant present a native reauthentication form when Tonal requires login again.
- Exposes a concise default set of Home Assistant sensors.
- Creates a much larger set of detailed sensors disabled by default so users can opt into richer data without entity clutter.
- Summarizes downloaded workout/set data locally; it does not create an entity for every historical set.
- Keeps the companion API local/private; no cloud relay or project telemetry is used.

## Home Assistant entities

Enabled by default:

- Strength Score
- Upper Strength Score
- Lower Strength Score
- Core Strength Score
- Workouts over 7 days
- Workouts over 30 days
- Volume over 7 days
- Volume over 30 days
- Total workouts
- Latest workout

Additional entities are created disabled by default and can be enabled from Home Assistant's entity registry. Depending on what Tonal returns for the account, these include:

- Lifetime volume, reps, sets, first workout, and days since last workout
- Latest workout volume, reps, sets, duration, type, movement count, max weight, estimated 1RM, ROM, and power where available
- 14/90/365-day workout and volume windows
- 7/30-day rep totals and average workout volume
- Best-observed workout volume, workout reps, set weight, 1RM, ROM, and power from downloaded history
- A recent-workouts entity with the ten most recent workout summaries as attributes
- Workout-type counts
- Strength Score history
- Strength Score regions and individual muscle Strength Scores returned by the API
- Service diagnostics such as last sync and service status

Some metrics depend on fields returned by Tonal and may be unavailable for older workouts or specific workout types. Record-style metrics are best values observed in the data returned to ToneGet; they are not claimed to be official Tonal PR records.

## Architecture

```text
Home Assistant app / UI
        |
        v
Home Assistant custom integration
        |
        | private local HTTP
        v
ToneGet companion service
        |
        | HTTPS authentication/data requests
        v
Tonal
```

The companion service should remain reachable only from the Home Assistant host, LAN, or private Docker network. Do not expose port 8787 publicly.

## Installation

### 1. Run the companion service

```bash
git clone https://github.com/jmping/tonalimporter.git
cd tonalimporter
cp docker-compose.example.yml docker-compose.yml
docker compose up -d --build
```

No Tonal password is stored in the Compose file. Before authentication, this should report `auth_required`:

```bash
curl http://127.0.0.1:8787/health
```

### 2. Install the Home Assistant custom integration

Copy:

```text
custom_components/tonal_companion/
```

into:

```text
/config/custom_components/tonal_companion/
```

Restart Home Assistant, then go to **Settings > Devices & services > Add Integration** and search for **ToneGet for Home Assistant**.

For a Docker-based Home Assistant installation on the same host, the companion URL will commonly be one of:

```text
http://tonalimporter:8787
http://host.docker.internal:8787
```

See [HA_SETUP.md](HA_SETUP.md) for more detail.

## Authentication and privacy

When authentication is required, Home Assistant presents email/password fields in its native UI. The credentials are sent over your private local connection to the companion service, used for the Tonal authentication exchange, and the password is not persisted by this project.

The companion service stores only returned Tonal token material in its private data volume. Treat that token as sensitive. No analytics, telemetry, or developer-hosted backend is used.

See [SECURITY.md](SECURITY.md) for security guidance.

## HACS

The custom integration includes HACS metadata for users who prefer HACS-based installation. During the beta period, manual installation remains the most predictable path because the companion service must still be deployed separately.

## ToneGet exporter

The original ToneGet command-line exporter remains available:

```bash
python3 -m pip install -r requirements.txt
python3 sync_workouts.py
```

It can export workout history, sets/reps/weights/volume, Strength Score data, custom workout metadata, and other workout metrics to JSON.

## Upstream attribution

This project is derived from the ToneGet project originally published at:

- https://github.com/curlrequests/toneget

The ToneGet exporter code and this fork are distributed under the MIT License. Existing upstream license and disclaimer terms are preserved in [LICENSE](LICENSE).

## Terms and service risk

This project relies on an unofficial authentication/API workflow. Tonal may change its API or authentication behavior at any time, and automated access may be restricted by Tonal's terms or technical controls. Use this software at your own risk and only with accounts/data you are authorized to access.

This project does not attempt to download or redistribute Tonal instructional videos, coaching content, or other proprietary service content.

## Development status

The Home Assistant integration is currently **beta software**. Before filing an issue, update to the latest release/branch and reproduce the problem. Do not post passwords, tokens, full exported workout files, or other sensitive personal data in issues.

## License

MIT License. See [LICENSE](LICENSE).
