# Guiyuan Vibecoding（中文说明）

## 通过 Agent 安装

已归档：GitHub 发布的 `v0.1.0` release zip 已停用。推荐从仓库安装：

```bash
git clone <your-repo-url> vibecoding_manager
cd vibecoding_manager
install.bat            # Windows
./install.sh           # macOS / Linux
```

仍要「发消息即装」：先用 `python tools/build_dist.py --verify` 打好
`dist/guiyuan-vibecoding-<version>.zip` 与 `.sha256`，自行托管后再把地址发给 Agent：

```text
请安装 Guiyuan Vibecoding Skill
技能地址：<你自行托管的 guiyuan-vibecoding-<version>.zip 地址>
```

Agent 安装时会校验 SHA-256、检查压缩包结构、备份旧的同名 Skill，并自检安装结果。

## 这是什么

Guiyuan Vibecoding 是一个本地优先的 AI 编码研发管理 Skill。它把项目引入一套可持续的迭代管理方式：启动规则、状态卡、变更台账、归档、确定性门禁和项目类型模板。

当前公开版本为 `0.1.0`，属于正式 1.0 之前的早期版本。早期内部标签 `v1.2.0` 只作为历史开发快照保留，不表示产品已达到 1.0。

## 当前能力

- 空目录：让用户用一句话描述想做什么，语义化识别为预设类型后引导创建新项目管理结构。
- 已有项目：先只读评估，再选择每个管理环节的保留、映射或托管。
- 低匹配度或发现同类系统：暂停并提示风险，由用户选择完全接管、只接管、保留并映射、延后接管或放弃。
- 接管前校验基线哈希，写入本地备份和回执。
- 业务代码不会被自动改写。

## 使用入口

1. 安装完成后，打开目标项目的新对话。
2. 显式调用 `$guiyuan-vibecoding`。
3. 告诉 Agent 项目位置、名称，并用一句话描述空目录项目想做什么。
4. 按提示完成语义确认、评估、门禁选择和接管确认。
5. 进入新对话开始第一轮真实任务。

安装位置按用户选择：共享 skills 目录、某个 Agent 的 skills 目录，或项目内
`.guiyuan-vibecoding/skills/`。技能正文是通用的 `SKILL.md`；`agents/openai.yaml` 只是 Codex
适配器，因此豆包、Harness、Codex 等兼容 Agent 可以共用同一份技能。

## 下载与更新

- 已停用 GitHub 公开 release zip；仓库直装为默认。
- 发消息安装仅适用于自行构建并托管的 zip；安装会校验 SHA-256、备份并被替换。
- Gitee raw 当前浏览器实测返回 Access denied，不再作为安装入口；Gitee 仍保留代码镜像仓库。

旧的发布地址与校验规则见（已归档）[docs/03-reference/release-sources.md](docs/03-reference/release-sources.md)。
