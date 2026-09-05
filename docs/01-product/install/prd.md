---
artifact_id: product/install
kind: product-spec
status: accepted
---
# Install Capability

用户可以从仓库或自托管包安装通用 Guiyuan Vibecoding Skill，并在安装前知道目标位置、备份和回滚行为。

产品对外只暴露一个 `guiyuan-vibecoding` 入口；安装、更新、卸载和迭代收尾作为内部路由，
按对话意图显式加载，不在全局 Skill 列表中制造额外入口。

安装能力同时覆盖技能安装、项目脚手架、更新、卸载和现有项目渐进接入；不拥有具体 Python/Node 实现。

卸载默认直接移除 VCM 自有组件（Skill、约束文档和 VCM 注册），不删除用户数据、插件、业务代码、
用户 Markdown 管理文档或 Butler MCP。发现相似 Skill 时必须先询问用户并优先共存。
