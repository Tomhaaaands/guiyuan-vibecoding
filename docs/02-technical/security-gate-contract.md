---
artifact_id: technical/security-gate
kind: technical-spec
status: accepted
supports: product/install, product/delivery
---
# Git 提交安全闸门

VCM 在项目创建或接管时生成分层 `.gitignore`：通用基础规则叠加 topology、scale 和 capability
规则。新项目直接生成；已有项目只追加缺失规则，不覆盖用户已有内容。

每次提交前，项目级 `.git/hooks/pre-commit` 先执行 `tools/git_safety_gate.py`，再执行
`tools/check_drift.py`。闸门读取 `git diff --cached` 的 staged snapshot，检查密钥模式、敏感
文件名、缓存/构建产物、越界符号链接、超大文件、非白名单二进制和提交压缩包。任一读取或规则
错误均失败关闭，输出规则编号、路径、行号和修复提示，不输出秘密原文。

本地 `git commit --no-verify` 只能视为紧急旁路；受保护主分支必须在 GitHub Actions 重跑同一
安全检查和 QA，且分支保护禁止绕过必需检查。Release 只能从通过这些检查的提交创建。

## 验收

```text
python tools/git_safety_gate.py
python tools/run_qa.py
```

无 staged 文件时闸门通过；`.env.example` 等明确示例文件可提交，真实 `.env`、凭据、缓存和
构建目录一律阻断。
