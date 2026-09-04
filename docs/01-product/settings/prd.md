---
artifact_id: product/settings
kind: product-spec
status: draft
---
# Settings Capability

用户可以通过 VCM 管理界面查看和修改 Provider、迁移确认等 VCM 设置。设置页只管理 VCM
行为，不接管宿主项目业务配置。

包含 `pb_enabled`（PB 赋能）开关：`off` 为独立 VCM（零模型、零向量，确定性检索 + LLM provider），
`on` 接入 PB 提供语义评分与用户上下文；PB 不可用时降级，不阻塞迭代循环。

设置落盘为项目内 `.guiyuan-vibecoding/config.json`，字段：

```json
{"schema_version": 1, "pb_enabled": false, "pb_endpoint": "http://192.168.2.123:8001", "pb_token": ""}
```

静态项目状态页会读取该文件并展示 VCM 接管状态；页面由
`python tools/render_project_home.py` 生成，直接打开项目根 `status.html`，不需要 8010
端口或常驻进程。Admin/Web 设置界面仍可作为可选的交互入口；PB 接入一律以
`private_butler/docs/api-contract.md` 为准（MCP `/mcp`、Bearer token、工具名 `guiyuan_butler_*`；
`similarity` 尚未实现，VCM 用关键词降级）。
