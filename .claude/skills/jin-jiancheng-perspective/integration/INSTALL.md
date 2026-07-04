# 融合到本地量化选股 agent team

本目录是集成套件：把「金渐成」从静态 skill 变成你 agent team 里的一名成员（风控/决策闸门）。

## 方式一：Claude Code 项目（推荐）

在你本地的 agentteam 项目根目录执行：

```bash
# 1. 拉取 skill 分支（PR 合并后可改用默认分支）
git clone --depth 1 -b claude/github-nuwa-skill-setup-0y0v8v \
  https://github.com/xxxavier524/graphify /tmp/jjc-skill

# 2. 安装 skill（思维框架）+ 子代理（团队成员）
mkdir -p .claude/skills .claude/agents
cp -r /tmp/jjc-skill/.claude/skills/jin-jiancheng-perspective .claude/skills/
cp .claude/skills/jin-jiancheng-perspective/integration/agents/jin-jiancheng-gatekeeper.md .claude/agents/

rm -rf /tmp/jjc-skill
```

装完后两种用法：

| 用法 | 触发方式 | 角色 |
|------|---------|------|
| **Skill**（对话人格） | 对 Claude 说「用金渐成的视角分析这份持仓」 | 思维顾问，你直接和他聊 |
| **Subagent**（团队成员） | 你的主 agent 在选股流水线里 spawn `jin-jiancheng-gatekeeper`，把候选标的列表交给它 | 决策闸门：战场过滤→周期定位→期望值→仓位→边界，输出放行/否决表 |

流水线接入点建议：放在「信号生成/回测」之后、「下单/组合构建」之前——所有候选必须过闸门才能进入组合。

## 方式二：非 Claude Code 框架（AutoGen / LangGraph / CrewAI 等）

skill 本质是一份自包含的 Markdown 认知框架，无运行时依赖：

1. 把 `SKILL.md` 全文作为风控 agent 的 **system prompt**
2. 把 `integration/agents/jin-jiancheng-gatekeeper.md` 正文（去掉 frontmatter）追加为该 agent 的任务指令
3. 团队编排：`选股信号 agent → 金渐成闸门 agent → 执行 agent`，闸门输出裁决表（放行/降仓放行/否决）

## 质量与迭代

- 质量门禁：`python3 scripts/quality_check.py SKILL.md`（当前 6/6 PASS）
- 迭代闭环：见 `LOOP.md`——有新语料（金渐成的文章/访谈）放入 `references/sources/` 后可用 /loop 自动增量蒸馏

> ⚠️ 思维框架模拟，不构成投资建议。
