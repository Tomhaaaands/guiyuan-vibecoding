# 归园 Guiyuan · 产品矩阵命名与标识对照

> 状态：accepted（2026-09-03）。本文件是“归园”产品矩阵的品牌命名与标识对照权威；品牌词、产品名、
> tagline 或前缀变更须同轮更新 PB / VCM / Creator OS 三仓副本；内部代码标识不随品牌改名而改。

## 1. 母品牌

- 中文：归园
- 英文/标识：`guiyuan`
- 意象：陶渊明《归园田居》——回到自己的园子、自给自足；对应“geek/自嘲式自留地”的产品气质。

## 2. 产品矩阵命名

| 产品 | 品牌名 | 标识 / MCP 前缀 | 内部仓库与代码标识 | tagline |
| --- | --- | --- | --- | --- |
| 个人记忆中枢 | 归园大管家 | `guiyuan_butler` | `private_butler` | 你的事我来管 |
| 自媒体 / AI 内容创作 | 归园自媒体 | `guiyuan_wemedia` | `tom_creator_os` | 内容创作平台 |
| 命理 / 卜算 | 归园算卦摊 | `guiyuan_bazi` | `suanming_os` | 给你起一卦 |
| 代码治理 / 编程管理 | 归园vibecoding | `guiyuan_vibecoding` | `vibecoding_manager` | 你讲思路，我撸代码 |

归园家族包含编程/代码治理一环：VCM 对外为 **归园vibecoding**（`guiyuan_vibecoding`），内部标识仍是
`vibecoding_manager`。

## 3. 命名规则

- 展示名、Agent Skill 名称与 MCP 前缀统一使用 `guiyuan` 前缀；仓库文件夹、Python 包名与 import 标识保留为兼容标识。
- VCM 对外只暴露 `guiyuan-vibecoding`；install 与 iteration-close-loop 是由它显式路由的内部模块。旧名称仅用于迁移识别。
- PB 的安装/更新适配器对外名称为 `guiyuan-butler-install`；其源码实现目录
  `packaging/one-line-install/` 是 PB 内部构建路径，不是用户项目配置目录。
- `guiyuan_butler` ↔ PB（`private_butler`）；`guiyuan_wemedia` ↔ Creator OS（`tom_creator_os`）；
  `guiyuan_bazi` ↔ suanming_os。
- 内部标识改名属独立、更高风险步骤，须单独评审，不得随品牌改名一并执行。

## 4. 桥接与 MCP

- PB 对外网关/显示名使用 `guiyuan_butler`（历史 MCP 前缀已迁移为 `guiyuan_butler_*`）。
- VCM ↔ PB 的正式接口是 `guiyuan_butler_similarity`、`guiyuan_butler_chat_context`、
  `guiyuan_butler_capture`；具体 JSON-RPC/鉴权/幂等契约以 PB 安装包内的
  `docs/api-contract.md` 为准。PB 不可达或 Embedding 不可用时，VCM 必须优雅降级、不阻塞。
- PB 独占其 Embedding/向量链路（当前部署可使用 bge-m3）；VCM 只通过 MCP 调用，不触碰 PB
  的 SQLite、向量文件或 Embedding 服务。
- Creator OS 当前仍维护自己的 Qwen3-Embedding/Chroma 链路；本命名文件的 PB 接口说明不代表
  Creator OS 已将其内部向量存储交给 PB。

## 5. 变更同步

品牌词、产品名、tagline 或前缀变更时，三仓（PB / VCM / Creator OS）的本文件副本必须同轮更新；
内部代码标识变更属于独立评审项。
