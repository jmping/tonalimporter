# v0.3.3-beta.1 release checklist

The release tag must be created **after** the final documentation PR is merged.

## Maintainer checks

1. Confirm CI, HACS validation, and Hassfest pass on the final `main` commit.
2. Open [Publish companion container workflow](https://github.com/jmping/tonalimporter/actions/workflows/publish-container.yml) and confirm a successful run publishing `edge`. If none ran after merging #13, use **Run workflow** on `main`. Do not assume a successful build means the package is publicly readable.
3. Open [GitHub Packages for jmping](https://github.com/jmping?tab=packages) and find the `tonalimporter` container. Under **Package settings → Change visibility**, make it **Public** if necessary. Newly created GHCR packages may default to private.
4. From an unauthenticated Docker client, verify `docker pull ghcr.io/jmping/tonalimporter:edge`. Confirm `linux/amd64` and `linux/arm64` appear in the manifest, e.g. `docker buildx imagetools inspect ghcr.io/jmping/tonalimporter:edge`.
5. Perform a clean HACS custom-repository install and verify the companion's `/health` endpoint and HA config flow. Check a real Tonal login and at least one completed synchronization. Never paste passwords or tokens into issues.
6. Where possible, confirm refresh token availability (presence only), renewal after ID-token expiration, and persistence after container recreation. These behaviors depend on Tonal/Auth0 and cannot be certified from unit tests alone.
7. Review branch protection on `main` and restore the intended minimal rules.

## Publish the GitHub release

1. Open [Releases](https://github.com/jmping/tonalimporter/releases) → **Draft a new release**.
2. Create new tag `v0.3.3-beta.1` **targeting `main`**, and title it `ToneGet for Home Assistant v0.3.3-beta.1`.
3. Paste the `v0.3.3-beta.1` section of [RELEASE_NOTES.md](RELEASE_NOTES.md) into the release description.
4. Mark it **Set as a pre-release** and publish.
5. Check the `Publish companion container` workflow ran for the new tag and that the corresponding GHCR version-tagged image exists. The workflow emits both the exact tag and a semver-derived tag.
6. Verify HACS recognizes the new beta release (beta channel may need enabling) and can upgrade the custom integration. The Docker companion is upgraded separately.

## After release

Complete the outstanding quality and real-device items in [HACS readiness issue #7](https://github.com/jmping/tonalimporter/issues/7). Then submit the repository to [hacs/default](https://github.com/hacs/default) using its current submission instructions and PR template. HACS defaults acceptance is a separate review and is not implied by successful HACS validation.
