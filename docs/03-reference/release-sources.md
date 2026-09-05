# Release Sources (archived)

> Status: current release `v0.1.2` (2026-09-05). The earlier GitHub-published `v0.1.0` zip release is retired. The kit is
> installed from the repository (`git clone` + `install.bat`/`install.sh`) or as a user-built zip
> that you host yourself. This file documents the retired distribution; it is not an active install
> source.

## Current published zip (v0.1.2)

The installable asset is published in the GitHub `v0.1.2` Release as
`guiyuan-vibecoding-0.1.2.zip`, with its `.sha256` companion and manifest. The archive root
contains exactly one discoverable Skill, `guiyuan-vibecoding`; install and close-loop are internal
payloads and do not create additional global entries.

注意：GitHub 自动附带的 `Source code (zip)` / `Source code (tar.gz)` 是完整仓库源码快照，
不是安装包；其中保留仓库侧的兼容性源码是正常的。对话安装只能使用上面的
`guiyuan-vibecoding-0.1.2.zip` 资产。

机器读取更新信息时使用仓库内的 [`update-catalog.json`](update-catalog.json)。每次发布准备
检测到新版本时，发布脚本会自动整合并更新该 catalog；它不是安装包本身，也不会替代
GitHub Release 的远端校验。

## Retired published zip (v0.1.0)

The public release asset `guiyuan-vibecoding-0.1.0.zip` and its `.sha256` were removed from the GitHub
release. The install-by-message flow is still valid, but the URL must come from a zip you build and
host:

```text
请安装 Guiyuan Vibecoding Skill
技能地址：<URL of a separately hosted guiyuan-vibecoding-<version>.zip>
```

Build it yourself:

```bash
python tools/build_dist.py --verify   # writes dist/guiyuan-vibecoding-<version>.zip + .sha256 + manifest
```

Host that zip where you control it, then send the message above. Verify the `.sha256` companion file
on install; update backs up existing skills and restores them if verification fails. GitHub proxy
mirrors only apply to the retired published asset and are no longer referenced.

## Old public line

The earlier `v1.2.0` tag is a historical development snapshot, not a current release. The current
version line is `0.1.x`.
