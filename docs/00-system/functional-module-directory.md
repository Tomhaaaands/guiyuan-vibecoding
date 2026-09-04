# 功能模块目录

这是给人看的 VCM 功能地图，也是 `status.html` 的结构化数据源。它描述“系统能做什么”，不替代产品事实、任务状态或验收记录。

## 模块清单

| 模块 | 一句话职责 | 主要入口 |
| --- | --- | --- |
| 项目接入与生命周期 | 预检、脚手架、接管、更新、卸载 | `skills/guiyuan-vibecoding/scripts/bootstrap.py` |
| 需求接收与分析 | 将自然语言整理为事实、假设、选项、决策与开放问题 | `tools/analysis.py` |
| 权威工件管理 | 保存产品、技术、决策、任务、状态与验收工件 | `tools/artifact_store.py` |
| 注册表与确认锚点 | 索引文档并为 REQ/PLAN/QA/RELEASE 留下哈希确认 | `tools/project_registry.py`、`tools/anchor.py` |
| 规划与任务编排 | 维护依赖、判断就绪任务、选择下一步 | `tools/task_graph.py` |
| 上下文构建与检索 | 按 L0/L1/L2 和 token 预算组装最小上下文 | `tools/context_compiler.py`、`tools/hydrate.py` |
| PB 可选桥接 | 将语义评分与个人上下文委托给 PB | `tools/pb_bridge.py` |
| 执行与验证 | 调用执行器，运行测试、门禁并生成回执 | `tools/receipt_loop.py`、`tools/run_qa.py` |
| 交付与发布 | 打包、校验、Git 交付和安装回滚 | `tools/build_dist.py`、`tools/check_package.py` |
| 状态页与设置 | 生成只读 `status.html`，提供设置/接管入口 | `tools/render_project_home.py` |
| 反思与经验回流 | 从回执提取经验、影子策略与可复用规则 | `tools/experience_loop.py`、`tools/distill.py` |
| 模板与能力 Overlay | 按拓扑、规模和能力生成项目骨架 | `skills/guiyuan-vibecoding/profiles/` |

## status.html 数据块

```json
{
  "functionalModules": [
    {"id": "intake", "name": "项目接入与生命周期", "plain": "把新项目或旧项目接入归园流程", "entry": "skills/guiyuan-vibecoding/scripts/bootstrap.py"},
    {"id": "analysis", "name": "需求接收与分析", "plain": "把一句话想法整理成可确认的事实与选择", "entry": "tools/analysis.py"},
    {"id": "brain", "name": "权威工件与上下文", "plain": "只读取必要的项目事实，控制上下文成本", "entry": "tools/context_compiler.py"},
    {"id": "planning", "name": "规划与任务编排", "plain": "按依赖选出下一件能做的事", "entry": "tools/task_graph.py"},
    {"id": "execution", "name": "执行、验证与交付", "plain": "做完就测试，留下可核对的回执", "entry": "tools/receipt_loop.py"},
    {"id": "reflection", "name": "反思与经验回流", "plain": "把踩过的坑沉淀成可复用做法", "entry": "tools/experience_loop.py"}
  ]
}
```

PB 说明：`tools/pb_bridge.py` 只是 provider 适配层；VCM 不执行 embedding、不持有 embedding 模型或向量数据库。PB 关闭或不可达时，VCM 仍使用本地确定性关键词检索完成独立运行。
