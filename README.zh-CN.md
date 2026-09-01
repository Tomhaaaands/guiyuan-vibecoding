# VibeCoding_Manager（中文说明）

## 通过 Agent 安装

请把下面整段发给你的 Agent：

```text
请安装 VibeCoding_Manager Skill
技能地址：https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip
```

如果 GitHub 无法访问，请改用国内镜像地址：

```text
请安装 VibeCoding_Manager Skill
技能地址：https://gitee.com/tomhands/vibecoding-manager/raw/main/releases/0.1.0/vibecoding-manager-0.1.0.zip
```

如果 Gitee 也无法访问，可改用 GitHub 代理：

```text
请安装 VibeCoding_Manager Skill
技能地址：https://gh-proxy.com/https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip
```

备用代理：

```text
请安装 VibeCoding_Manager Skill
技能地址：https://ghfast.top/https://github.com/Tomhaaaands/vibecoding-manager/releases/download/v0.1.0/vibecoding-manager-0.1.0.zip
```

Agent 安装时会校验 SHA-256、检查压缩包结构、备份旧的同名 Skill，并自检安装结果。

## 这是什么

VibeCoding_Manager 是一个本地优先的 AI 编码研发管理 Skill。它把项目引入一套可持续的迭代管理方式：启动规则、状态卡、变更台账、归档、确定性门禁和项目类型模板。

当前公开版本为 `0.1.0`，属于正式 1.0 之前的早期版本。早期内部标签 `v1.2.0` 只作为历史开发快照保留，不表示产品已达到 1.0。

## 当前能力

- 空目录：引导创建新项目管理结构。
- 已有项目：先只读评估，再选择每个管理环节的保留、映射或托管。
- 低匹配度或发现同类系统：暂停并提示风险，由用户选择完全接管、只接管、保留并映射、延后接管或放弃。
- 接管前校验基线哈希，写入本地备份和回执。
- 业务代码不会被自动改写。

## 使用入口

1. 安装完成后，打开目标项目的新对话。
2. 显式调用 `$vibe-coding-manager`。
3. 告诉 Agent 项目位置和名称。
4. 按提示完成评估、门禁选择和接管确认。
5. 进入新对话开始第一轮真实任务。

## 下载与更新

- GitHub 是权威版本地址。
- 国内镜像使用 Gitee 仓库 raw 文件，非登录用户可直接下载；文件必须与 GitHub 完全一致。
- 国内回退顺序：Gitee raw → gh-proxy.com → ghfast.top，每次仍校验 SHA-256。
- 更新时重新发送新版本安装消息，Agent 会备份旧版本并在校验失败时回滚。

完整发布地址和校验规则见 [docs/release-sources.md](docs/release-sources.md)。
