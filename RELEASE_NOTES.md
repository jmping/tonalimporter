# Release notes

## v0.3.3-beta.1

Release candidate for the next public beta of **ToneGet for Home Assistant**.

### Authentication and recovery

- Added refresh-token support when Tonal/Auth0 returns a refresh token.
- Refreshes saved authentication and retries synchronization before requiring a password again.
- Distinguishes confirmed authentication failures from transient network/API failures.
- Stops clearing saved token material on generic errors that merely contain words such as `token`.
- Adds a consecutive authentication-failure threshold, defaulting to three failures before Home Assistant is asked to reauthenticate.
- Keeps saved credentials after the reauthentication threshold so the companion can continue retrying automatically.
- Clears `auth_required` and the failure counter automatically if those saved credentials begin working again.
- Preserves rotated or non-rotated refresh tokens returned by the service.

### HACS and Home Assistant readiness

- Added HACS validation and Home Assistant Hassfest workflows.
- Added packaged English translations and aligned the integration display name with **ToneGet for Home Assistant**.
- Added manifest metadata including `issue_tracker`, `codeowners`, and `integration_type`.
- Restored a standard MIT `LICENSE` file and separated supplemental disclaimer text into `DISCLAIMER.md`.
- Repository metadata now includes HACS-friendly topics and an updated description.
- HACS validation, Hassfest, and CI all pass on the release-preparation branch.

### Installation and upgrades

HACS installs and updates the Home Assistant custom integration only.

The companion service remains a separate local Docker service. Releases that contain companion changes still require updating the local checkout and rebuilding/restarting the companion container.

### Documentation

- Updated setup, contribution, security, and release documentation to match the current architecture and authentication behavior.
- Clarified the separation between the MIT license and supplemental disclaimer.
- Clarified the HACS-versus-companion upgrade path.

### Beta caveats

- The project relies on an unofficial Tonal authentication/API workflow and can break if Tonal changes its service.
- Some metrics depend on fields present in the data returned for a particular account or workout type.
- This remains community-built, vibecoded beta software and benefits from independent review and testing.

### Attribution

This repository is derived from the community ToneGet exporter at `curlrequests/toneget`. Tonal and Home Assistant trademarks belong to their respective owners.

---

## v0.3.1-beta.1

First public beta of **ToneGet for Home Assistant**.

### What this is

This is an unofficial, community-built bridge between **ToneGet** and **Home Assistant**. It was developed collaboratively with an AI coding assistant (in other words: vibecoded), then iterated against a real Home Assistant installation.

It is not affiliated with, endorsed by, or supported by Tonal Systems, Inc. or the Home Assistant project.

### Highlights

- Home Assistant custom integration with native config and reauthentication flows.
- Local companion service for Tonal authentication and data retrieval.
- HACS custom-repository installation tested end-to-end.
- Bundled Home Assistant integration artwork.
- Tonal password is not stored in Git, Docker Compose, HA YAML, or the HA config entry.
- Core workout and Strength Score entities enabled by default.
- Richer workout, lifetime, recent-workout, service, region, and muscle metrics available as opt-in entities disabled by default.
- Rolling 7/14/30/90/365-day workout and volume summaries.
- Rep totals, average workout volume, latest-workout details, and best-observed values derived from downloaded history where fields are available.
- Bounded recent-workout and movement attributes to avoid creating thousands of Home Assistant entities.
- Docker Compose deployment example for the companion service.
- CI validation on Python 3.12 and 3.13, including aggregation tests, linting, metadata checks, and Compose validation.

### Installation model

HACS installs the Home Assistant custom integration. The ToneGet companion service remains a separate local Docker service and must be deployed separately.

The companion API is intended for a trusted private network only. Do not expose port 8787 directly to the public internet.

### Beta caveats

- This project relies on an unofficial Tonal authentication/API workflow and can break if Tonal changes its service.
- Some metrics depend on fields present in individual Tonal workout payloads and may be unavailable for older workouts or workout types.
- Best-observed values are calculated from data returned to ToneGet and are not presented as official Tonal PR records.
- This is vibecoded beta software: useful and tested, but not a substitute for conventional independent code review. Contributions, audits, and bug reports are welcome.

### Privacy and security

- Passwords are used only during the authentication exchange and are not persisted by this project.
- Returned Tonal token material is stored locally by the companion service and should be treated as sensitive.
- No project telemetry, cloud relay, analytics service, or developer-hosted backend is used.
- Home Assistant itself may record enabled entity state/history in its database and backups.

### Attribution

This repository is derived from the community ToneGet exporter at `curlrequests/toneget` and preserves its MIT License and disclaimer. Tonal and Home Assistant trademarks belong to their respective owners.
