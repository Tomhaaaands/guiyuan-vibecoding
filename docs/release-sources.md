# Release Sources (archived)

> Status: archived (2026-09-03). The GitHub-published `v0.1.0` zip release is retired. The kit is
> installed from the repository (`git clone` + `install.bat`/`install.sh`) or as a user-built zip
> that you host yourself. This file documents the retired distribution; it is not an active install
> source.

## Retired published zip (v0.1.0)

The public release asset `vibecoding-manager-0.1.0.zip` and its `.sha256` were removed from the GitHub
release. The install-by-message flow is still valid, but the URL must come from a zip you build and
host:

```text
请安装 VibeCoding_Manager Skill
技能地址：<URL of a separately hosted vibecoding-manager-<version>.zip>
```

Build it yourself:

```bash
python tools/build_dist.py --verify   # writes dist/vibecoding-manager-<version>.zip + .sha256 + manifest
```

Host that zip where you control it, then send the message above. Verify the `.sha256` companion file
on install; update backs up existing skills and restores them if verification fails. GitHub proxy
mirrors only apply to the retired published asset and are no longer referenced.

## Old public line

The earlier `v1.2.0` tag is a historical development snapshot, not a current release. The current
version line is `0.1.x`.
