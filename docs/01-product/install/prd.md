---
artifact_id: product/install
kind: product-spec
status: accepted
---
# Install Capability

用户可以从仓库或自托管包安装通用 Guiyuan Vibecoding 技能，并在安装前知道目标位置、备份和回滚行为。

安装能力同时覆盖技能安装、项目脚手架、更新、卸载和现有项目渐进接入；不拥有具体 Python/Node 实现。

卸载默认直接移除 VCM 自有组件（Skill、约束文档和 VCM 注册），不删除用户数据、插件、业务代码、
用户 Markdown 管理文档或 Butler MCP。发现相似 Skill 时必须先询问用户并优先共存。
