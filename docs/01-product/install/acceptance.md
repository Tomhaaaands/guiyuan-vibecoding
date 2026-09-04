# Install Acceptance

- 安装前展示目标目录、版本、校验和以及是否覆盖已有技能。
- 安装失败时恢复备份，不留下半完成状态。
- 脚手架保留空的 `docs/00-system..04-workflow`、`apps/`、`workers/` 目录。
- 现有项目接入先只读审计，再由用户选择 `keep`、`map` 或 `managed`。
- 卸载默认只移除可证明属于 Guiyuan Vibecoding 的组件；相似 Skill、用户 Skill、插件、项目文件和 Butler MCP 保持不变。
- 无 Skill 但已有 Markdown 管理骨架的项目识别为 `md-managed`，继续走 `keep`、`map`、`managed` 门禁。
