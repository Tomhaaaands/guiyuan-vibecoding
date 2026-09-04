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
| 个人记忆中枢 | 归园大管家 | `guiyuan_butler` | `private_butler` | 你的事，我来管 / your business is my business |
| 自媒体 / AI 内容创作 | 归园自媒体 | `guiyuan_wemedia` | `tom_creator_os` | 内容创作平台 |
| 命理 / 卜算 | 归园算卦摊 | `guiyuan_bazi` | `suanming_os` | 给你起一卦 |
| 代码治理 / 编程管理 | 归园撸代码 | `guiyuan_vibecoding` | `vibecoding_manager` | 你讲思路，我撸代码 |

归园家族包含编程/代码治理一环：VCM 对外为 **归园撸代码 · Guiyuan Vibecoding**（`guiyuan_vibecoding`），
内部标识仍是 `vibecoding_manager`。

## 3. 命名规则

- 展示名、Agent Skill 名称与 MCP 前缀统一使用 `guiyuan` 前缀；仓库文件夹、Python 包名与
  import 标识保留为兼容标识，不作为用户入口。
- VCM 对外 Skill 名称固定为 `guiyuan-vibecoding`、`guiyuan-vibecoding-install`、
  `guiyuan-iteration-close-loop`；旧 `vibe-coding-*` 仅用于迁移识别，不再作为新入口。
- `guiyuan_butler` ↔ PB（`private_butler`）；`guiyuan_wemedia` ↔ Creator OS（`tom_creator_os`）；
  `guiyuan_bazi` ↔ suanming_os。
- 内部代码标识改名属独立、更高风险步骤；本轮只完成对外名称和 Skill 包名迁移。

## 4. 桥接与 MCP

- PB 对外网关/显示名使用 `guiyuan_butler`；权威接入契约见 `private_butler/docs/api-contract.md`
  （MCP `POST /mcp`、Bearer token、`guiyuan_butler_*` 工具、健康探活 `/healthz`）。
- VCM ↔ PB 接口：`guiyuan_butler_chat_context`（背景上下文）、`guiyuan_butler_capture`（幂等结果回流）；
  `similarity(query, texts[])` 尚未实现，VCM 用关键词降级，不得用 `guiyuan_butler_search` 顶替。
- embedding/向量全部由 PB 承载（bge-m3 + 向量库）；VCM 仅 `pb_enabled` 开关接入，不触碰向量。

## 5. 变更同步

品牌词、产品名、tagline 或前缀变更时，三仓（PB / VCM / Creator OS）的本文件副本必须同轮更新；
内部代码标识变更属于独立评审项。
