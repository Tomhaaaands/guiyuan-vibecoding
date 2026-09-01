# Release Sources

> Authoritative source is GitHub. Domestic users may fall back to the Gitee raw mirror or a GitHub
> proxy after verifying the same SHA-256.

## Current public line: 0.1.x

The previous `v1.2.0` tag remains a historical development snapshot. New releases start at
`0.1.0` and continue as `0.1.x` until the product reaches a 1.0 release bar.

## v0.1.0 assets

| Source | URL |
| --- | --- |
| GitHub (authoritative) | https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip |
| GitHub SHA-256 | https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip.sha256 |
| GitHub proxy 1 (gh-proxy.com) | https://gh-proxy.com/https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip |
| GitHub proxy 1 SHA-256 | https://gh-proxy.com/https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip.sha256 |
| GitHub proxy 2 (ghfast.top) | https://ghfast.top/https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip |
| GitHub proxy 2 SHA-256 | https://ghfast.top/https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip.sha256 |

The Gitee repository and Release are published under `tomhands/vibecoding-manager`. Public web
access should be verified from a normal browser; some automated environments may receive a 403
from Gitee's anti-bot layer while the Gitee API still serves the original files. The Gitee raw
path under `releases/0.1.0/` returned `Access denied` in a browser test, so it is not an install
source.

Domestic fallback order: `gh-proxy.com` -> `ghfast.top`. Proxy services are third-party and may
change; always verify the downloaded zip against the published SHA-256.

## Install message

```text
请安装 VibeCoding_Manager Skill
技能地址：<URL from the GitHub or Gitee row above>
```

## Verification rules

1. Download the zip and its `.sha256` companion file.
2. Verify that the zip hash matches the published checksum.
3. Confirm the zip root contains exactly `iteration-close-loop/`, `vibe-coding-manager/`, and
   `vibe-coding-install/`.
4. Verify `vibe-coding-install/VERSION` matches `0.1.0`.
5. Back up existing same-named skills before replacement; restore the backup if verification fails.
