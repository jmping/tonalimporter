# Release notes

## v0.2.0-beta.1 (planned)

First public beta of **ToneGet for Home Assistant**.

### Highlights

- Home Assistant custom integration with native config and reauthentication flows.
- Local companion service for Tonal authentication/data retrieval.
- Tonal password is not stored in Git, Docker Compose, HA YAML, or the HA config entry.
- Core workout and Strength Score entities enabled by default.
- Richer workout/service/muscle entities available as opt-in entities disabled by default.
- HACS metadata for custom-repository installation.
- Docker Compose deployment example for the companion service.
- CI validation for Python, JSON metadata, and Compose configuration.

### Important security note

The companion API is intended for a trusted private network only. Do not expose port 8787 directly to the public internet.

### Project status

This is beta software built on an unofficial API workflow. Tonal may change authentication or API behavior without notice.

### Attribution

This repository is derived from the community ToneGet exporter and preserves its MIT License and disclaimer. This project is not affiliated with or endorsed by Tonal Systems, Inc.
