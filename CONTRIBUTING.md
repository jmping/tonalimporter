# Contributing to ToneGet for Home Assistant

Thank you for considering a contribution. ToneGet for Home Assistant is an unofficial community project that combines three related pieces:

- the original ToneGet-style personal workout exporter (`sync_workouts.py`);
- a local companion service (`tonal_service.py`) that handles authentication, synchronization, and summary generation;
- a Home Assistant custom integration under `custom_components/tonal_companion/`.

The project is intentionally open to review and improvement. The Home Assistant bridge was developed collaboratively with an AI coding assistant, then iterated against a real installation, so careful human review, testing, and simplification are especially welcome.

## Before you start

Please read [SECURITY.md](SECURITY.md) before changing authentication, token handling, networking, logging, or diagnostics.

Do not include passwords, access tokens, refresh tokens, raw workout exports, email addresses, workout IDs, or other private account data in issues, pull requests, tests, screenshots, or logs.

This project is not affiliated with, endorsed by, or supported by Tonal Systems, Inc. Contributions must not imply official Tonal support or branding.

## Project layout

```text
tonalimporter/
├── custom_components/tonal_companion/   # Home Assistant integration
├── tests/                               # regression/unit tests
├── sync_workouts.py                     # standalone exporter
├── tonal_service.py                     # local companion HTTP service
├── docker-compose.example.yml           # companion deployment example
├── HA_SETUP.md                          # Home Assistant setup details
├── README.md
├── RELEASE_NOTES.md
├── SECURITY.md
└── CONTRIBUTING.md
```

## Reporting bugs

Use the GitHub bug-report template when possible. Include:

- Home Assistant version;
- ToneGet for Home Assistant version or commit;
- installation type;
- companion deployment method;
- exact reproduction steps;
- sanitized logs;
- expected and observed behavior.

If the problem concerns authentication, say whether the companion currently reports `auth_required`, but never post token contents.

## Suggesting features

Open a feature request and describe the user-facing problem first. For new Home Assistant entities, also note whether the entity should be enabled by default or opt-in.

Prefer deriving additional metrics from data already downloaded by the companion instead of adding unnecessary Tonal API calls.

## Submitting code

1. Fork the repository.
2. Create a focused branch.
3. Make the smallest coherent change.
4. Add or update tests where practical.
5. Run the validation steps below.
6. Open a pull request against `main`.

Keep pull requests narrowly scoped. Large refactors should explain why they are necessary and how compatibility is preserved.

## Development setup

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install ruff pytest
```

On Windows, activate the virtual environment with the equivalent `venv\Scripts\activate` command.

## Validation

Before opening a pull request, run as much of the following as your environment supports:

```bash
python -m compileall -q sync_workouts.py tonal_service.py custom_components/tonal_companion tests
ruff check tonal_service.py custom_components/tonal_companion tests --ignore EXE001,UP006,UP035,UP045,RUF100,UP031
python -m pytest -q tests
docker compose -f docker-compose.example.yml config
```

GitHub Actions also runs:

- CI on Python 3.12 and 3.13;
- HACS validation;
- Home Assistant Hassfest validation.

Pull requests should leave all three green unless there is a documented reason a check cannot apply.

## Home Assistant conventions

For changes under `custom_components/tonal_companion/`:

- keep entity IDs and unique IDs stable whenever possible;
- use Home Assistant-native config-entry and reauthentication patterns;
- prefer disabled-by-default entities for niche or attribute-heavy data;
- avoid unbounded attributes that could inflate the recorder database;
- use appropriate device classes, state classes, and units where applicable;
- keep `strings.json` and packaged translations consistent;
- do not expose tokens or private workout payloads in diagnostics.

## Companion-service conventions

The companion service is local infrastructure, not a public internet service.

- Keep authentication and summary endpoints private by default.
- Do not add public exposure as a default.
- Treat saved token material as sensitive.
- Preserve refresh-token support and retry/recovery behavior.
- Distinguish authentication failures from transient API/network failures.
- Do not clear usable saved credentials merely because one sync attempt failed.
- Avoid additional Tonal requests when equivalent data can be computed locally.

## Security and privacy

Security-sensitive changes should be conservative.

- Never log credentials or token material.
- Never commit real account data.
- Use HTTPS for external Tonal/Auth0 requests.
- Sanitize exception messages before exposing them to Home Assistant.
- Keep the local companion API constrained to a trusted host/LAN/private network.
- Do not add analytics, telemetry, or a developer-hosted relay without explicit discussion.

## Scope

Good contributions include:

- bug fixes and regression tests;
- Home Assistant compatibility improvements;
- better auth-recovery behavior;
- additional locally derived metrics;
- documentation improvements;
- recorder-impact reductions;
- diagnostics that are safe to share;
- packaging and release improvements.

Out of scope includes:

- bulk scraping or access to other users' data;
- redistribution of Tonal instructional media or proprietary service content;
- features designed to bypass account controls or platform restrictions;
- changes that expose the companion service publicly by default.

## Licensing and attribution

Contributions are accepted under the repository's MIT License. This fork is derived from the community ToneGet project; preserve applicable attribution and do not remove upstream history merely for cosmetic reasons.

See [DISCLAIMER.md](DISCLAIMER.md) for supplemental project guidance.

## Questions

If something is unclear, open an issue. For security-sensitive matters, follow the private-reporting guidance in [SECURITY.md](SECURITY.md).
