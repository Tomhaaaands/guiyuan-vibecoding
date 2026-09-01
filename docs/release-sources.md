# Release Sources

> Authoritative source is GitHub. Domestic users may fall back to the Gitee mirror after verifying
> the same SHA-256.

## Current public line: 0.1.x

The previous `v1.2.0` tag remains a historical development snapshot. New releases start at
`0.1.0` and continue as `0.1.x` until the product reaches a 1.0 release bar.

## v0.1.0 assets

| Source | URL |
| --- | --- |
| GitHub (authoritative) | https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip |
| GitHub SHA-256 | https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip.sha256 |
| Gitee mirror | https://gitee.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip |
| Gitee SHA-256 | https://gitee.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip.sha256 |

The Gitee repository and Release must be created by the repository owner before the mirror links
are live. Replace the owner in the URL only if the Gitee account name differs from `Tomhaaaands`.

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
