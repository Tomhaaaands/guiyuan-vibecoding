---
artifact_id: technical/packaging/install
kind: technical-spec
status: accepted
supports: [product/install]
---
# Install Technical Contract

安装器必须校验版本与校验和、备份同名目录、失败可恢复，并把目标路径作为显式配置；技能
正文保持 Agent 中立，`agents/openai.yaml` 仅是可选适配器。
