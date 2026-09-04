# 功能模块目录

这是给人看的项目功能地图，也是 `status.html` 的结构化数据源。脚手架会保留此文件，状态页读取其中的 `functionalModules` 数据块。

## 模块清单

| 模块 | 一句话职责 | 主要入口 |
| --- | --- | --- |
| 项目接入与生命周期 | 预检、脚手架、接管、更新、卸载 | `tools/bootstrap.py` |
| 需求接收与分析 | 将自然语言整理为事实、假设、选项、决策与开放问题 | `tools/analysis.py` |
| 权威工件与上下文 | 保存项目事实并按预算组装最小上下文 | `tools/artifact_store.py`、`tools/context_compiler.py` |
| 规划与任务编排 | 维护依赖、判断就绪任务、选择下一步 | `tools/task_graph.py` |
| 执行、验证与交付 | 执行代码、测试门禁、生成回执并交付 | `tools/receipt_loop.py`、`tools/run_qa.py` |
| 反思与经验回流 | 从回执提取经验、影子策略与可复用规则 | `tools/experience_loop.py` |
| 模板与能力 Overlay | 按拓扑、规模和能力生成项目骨架 | `.guiyuan-vibecoding/project-manifest.toml` |

## status.html 数据块

```json
{"functionalModules":[{"id":"intake","name":"项目接入与生命周期","plain":"把项目接入归园流程","entry":"tools/bootstrap.py"},{"id":"analysis","name":"需求接收与分析","plain":"把想法整理成可确认的事实与选择","entry":"tools/analysis.py"},{"id":"brain","name":"权威工件与上下文","plain":"只读取必要的项目事实，控制上下文成本","entry":"tools/context_compiler.py"},{"id":"planning","name":"规划与任务编排","plain":"按依赖选出下一件能做的事","entry":"tools/task_graph.py"},{"id":"execution","name":"执行、验证与交付","plain":"做完就测试并留下回执","entry":"tools/receipt_loop.py"},{"id":"reflection","name":"反思与经验回流","plain":"把踩过的坑沉淀成可复用做法","entry":"tools/experience_loop.py"}]}
```

PB 只是 provider 适配层：VCM 不执行 embedding、不持有模型或向量数据库。PB 关闭或不可达时，项目仍使用本地关键词检索运行。
