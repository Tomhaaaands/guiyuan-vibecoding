---
artifact_id: technical/vcm-module
kind: technical-spec
status: accepted
supports: [product/analysis, product/dispatch, product/delivery, product/install]
---

# VCM 内部职责模块契约

VCM 是一个模块化单体：代码按职责分包，但仍由一个 `guiyuan-vibecoding` Skill 暴露。模块
可以独立调用，也可以由 `vcm_workflow` 串联；模块之间不共享未声明的内部路径或事实副本。

## 目录与边界

| 包 | 责任 |
| --- | --- |
| `vcm_core` | artifact store、manifest、registry、anchor、上下文预算、协议 |
| `vcm_requirement` | 需求分析、provider/label、需求 artifact 与一致性 |
| `vcm_planning` | task graph、依赖/ready 判定、context compiler、hydrate |
| `vcm_workflow` | 总编排、receipt、experience、MVP walkthrough、项目状态恢复 |
| `vcm_qa` | 单元/行为/漂移/打包/架构与聚合门禁 |
| `vcm_release` | release prepare、git safety、构建、catalog、同步与发布准备 |
| `vcm_install` | Skill 安装、更新、one-click 与项目 hook |
| `vcm_uninstall` | manifest-owned 安全卸载 |

根目录 `tools/*.py` 保留为兼容导入/CLI 包装，不再承载实现。公共发现面不增加新的
`SKILL.md`；close-loop 载荷仍只在选择项目工作流时物化。

## 稳定结果协议 v1

每个需要跨模块交接的调用返回以下外壳：

```yaml
module_id: requirement
contract_version: v1
status: complete|ready|blocked|failed
artifacts: []
evidence: []
blockers: []
next_action: ""
```

`artifacts` 只放稳定 artifact id、路径引用或小型结果；`evidence` 放可复核的命令/报告；
`blockers` 必须说明缺失门禁或输入；`next_action` 是给上层路由器的下一步。用户确认、仓库
事实、推断和当前假设仍按原有事实所有权分开保存。

## 状态与门禁

内部状态保持 `INTAKE → ANALYSIS → SPECIFICATION → PLANNING → EXECUTION → VERIFICATION →
DELIVERY → REFLECTION → NEXT`。对外只显示“需求收敛 → 计划形成 → 执行交付 → QA/发布”。
`vcm_workflow` 可以恢复状态、转入 repair 或记录 blocked，但不能跳过 requirement、planning、
QA 或 release 门禁。

## 设计扩展点

VCM 不伪造设计完成态，也不引入视觉规则。未来 `guiyuan-design` 可读取 requirement-pack
和 plan，并以同一协议返回设计资产；VCM 将其视为可选 provider，缺失时继续代码优先闭环。
