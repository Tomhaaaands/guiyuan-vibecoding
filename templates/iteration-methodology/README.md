# 迭代方法论模板（templates/iteration-methodology）

> 来源：Creator OS R102 方法论沉淀。可复制到任何新项目，替换占位符后即获得一套
> 「AI 主导开发」迭代闭环：启动契约 + 一行台账 + 档案分卷 + 状态卡 + 机械门禁。

## 包含什么

```text
AGENTS.md                       # 启动契约骨架（必读顺序/路由表/纪律/索引）
docs/04-workflow/
  AGENTS_WORKFLOW.md            # 流程骨架（路由表/双工作流/五步闭环/变更映射）
  changelog.md                  # 一行台账骨架
  NOW.md                        # 当前焦点状态卡骨架（焦点/阻塞/下一步）
  iteration-methodology.md      # 完整方法论（可直接复用）
  archive/README.md             # 档案分卷规则
tools/
  rollup_round.py               # 生成档案分卷 + 插入台账行
  hydrate.py                    # 按关键词渐进检索 docs
  check_drift.py                # 扫描过期标记 + 校验 llms.txt 链接
  gen_llms_txt.py               # 生成根目录 llms.txt 文档索引
```

## 落地三步

1. **复制**：把本目录内容复制到新项目根目录；
2. **填占位符**：替换 `{{PROJECT_NAME}}`；按项目裁剪 AGENTS.md §1 路由表与 §3 技术约束；
   把「最小闭环四件套」首行写进 changelog（可用 `python tools/rollup_round.py --round R1 ...`）；
3. **生成索引**：`python tools/gen_llms_txt.py` 生成 llms.txt；收尾跑
   `python tools/check_drift.py` 与项目自身的结构校验。

> 使用 `$project-bootstrap` 一键部署时，可在对话中逐个提供业务模块
> （名称/关键词/代码目录），脚本会用 `--module "名称=关键词" --code "名称=目录"`
> 自动填好 AGENTS.md 与 AGENTS_WORKFLOW.md 的路由表。

## 可选：行为封装

把方法论装成本地 skill 后，任何项目触发即用：
`$iteration-close-loop` 负责收尾闭环，`$project-bootstrap` 负责一键部署
（本模板已随包分发，新项目第一条对话自动复制骨架、写 R1、生成索引并安装闭环 skill）。

## 与完整方法论的关系

完整原则与迁移指南见 `docs/04-workflow/iteration-methodology.md`（第 11 节）；
本模板 = 最小集（四件套）+ 标准集（工具链）的实体化。
