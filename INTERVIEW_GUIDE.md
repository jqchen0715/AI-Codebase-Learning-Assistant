# INTERVIEW_GUIDE

这份文档用于面试前快速掌握本项目，并把技术实现讲成“AI Agent 应用岗位”可识别的能力。

## 1) 项目一句话定位

`AI Codebase Learning Assistant` 是一个多节点 Agent Workflow：输入 GitHub 仓库或本地代码目录，自动生成教程、源码阅读路线、面试问答和项目掌握度报告，把“读不懂项目”变成可执行学习闭环。

## 2) 你要讲的业务价值

- 传统文档生成器只“解释代码”，本项目额外提供“怎么学、怎么面试、怎么检验掌握度”。
- 输出面向真实求职动作：`code_reading_route.md`、`interview_qa.md`、`project_mastery_report.md`。
- 支持用户画像参数化：学习者等级、面试方向、掌握周期。

## 3) 5 分钟快速过代码结构

### 3.1 入口

- CLI 入口：`main.py`
- Flow 组装：`flow.py`
- 节点实现：`nodes.py`
- LLM 调用：`utils/call_llm.py`

### 3.2 主流程（按执行顺序）

1. `FetchRepo`
2. `IdentifyAbstractions`
3. `AnalyzeRelationships`
4. `OrderChapters`
5. `GenerateCodeReadingRoute`
6. `GenerateInterviewQA`
7. `GenerateProjectMasteryReport`
8. `WriteChapters`（BatchNode）
9. `CombineTutorial`

可以直接在 [flow.py](/Users/jiaqing/八股/ai-agent-interview-guide/project/PocketFlow-Tutorial-Codebase-Knowledge/flow.py) 对照讲这条链路。

### 3.3 关键 shared state（面试必讲）

- 输入类：`repo_url/local_dir`、`language`、`learner_level`、`interview_focus`、`mastery_horizon`
- 中间产物：`abstractions`、`relationships`、`chapter_order`
- 输出产物：`code_reading_route`、`interview_qa`、`project_mastery_report`、`chapters`

这是典型的“有状态 Agent Workflow”设计，不是单轮 Prompt。

## 4) 你应该掌握的 5 个核心维度（面试官高频）

### 4.1 项目入口

- 讲清参数如何影响行为：
  - `--learner-level` 影响解释深度
  - `--interview-focus` 影响问答偏置
  - `--mastery-horizon` 影响掌握计划长度（3/7/14天）

### 4.2 核心数据流

- 文件抓取 -> 抽象识别 -> 关系推断 -> 章节排序
- 再生成三类“学习辅助资产”：阅读路线、面试问答、掌握报告
- 最后统一写入 `index.md + 多 md 文件`

### 4.3 关键模块职责

- `IdentifyAbstractions`：抽象候选 + 关联文件索引
- `AnalyzeRelationships`：生成项目摘要和抽象关系图数据
- `GenerateInterviewQA`：基于 `interview_focus` 生产面试问答
- `GenerateProjectMasteryReport`：把理解目标转成可执行学习计划和 checklist
- `CombineTutorial`：统一聚合输出并注入导航链接

### 4.4 可扩展点

- 增加新产物节点：按 `prep/exec/post` 加入 Flow
- 增加新用户画像参数：CLI -> shared -> 节点 prompt
- 增加模型后端：扩展 `utils/call_llm.py` 的 provider 分支

### 4.5 面试高频问题

- 为什么不用一个超大 prompt 一次生成全部？
  - 因为多节点可以解耦目标、增强可控性、支持重试和定向优化。
- 为什么用 `chapter_order` 而不是按文件树顺序？
  - 文件树顺序不等于理解顺序，`chapter_order` 是“认知顺序”。
- `BatchNode` 的价值？
  - 章节天然可分治，减少上下文污染，便于并行/重试。

## 5) 你可以直接背的 60 秒介绍

“我做了一个 AI Agent 学习助手，目标是解决上手陌生代码仓和实习面试准备效率低的问题。技术上不是单次文档生成，而是一个有状态的多节点 workflow：先抓代码，识别核心抽象和关系，再按理解顺序生成教程；同时生成源码阅读路线、面试问答和掌握度报告。这个系统支持学习者等级、面试方向和学习周期参数化，能把输出从通用说明升级为可执行的学习与面试准备计划。”

## 6) 演示脚本（面试机上可跑）

### 6.1 快速命令

```bash
python main.py \
  --repo https://github.com/username/repo \
  --learner-level intermediate \
  --interview-focus agent-framework \
  --mastery-horizon 7d
```

### 6.2 演示顺序

1. 打开 `index.md`（总览）
2. 打开 `code_reading_route.md`（先读哪里）
3. 打开 `interview_qa.md`（怎么讲给面试官）
4. 打开 `project_mastery_report.md`（如何在 7 天掌握）

## 7) 面试官追问与回答模板

### Q1: 你如何保证生成内容不胡编？

- 回答模板：
  - “我把上下文限定在抓取到的文件索引和关系图数据上，节点间只传结构化结果。并且在抽象和关系阶段做了 YAML 解析与索引校验，减少无约束自由生成。”

### Q2: 这个项目最难的技术点是什么？

- 回答模板：
  - “难点在把‘学习目标’拆成可组合节点，并让每个节点输出可被下游消费。比如问答和掌握报告都依赖前面抽象/关系/章节顺序，这要求 shared state 设计一致且稳定。”

### Q3: 你做过哪些产品化增强？

- 回答模板：
  - “我加了学习者等级、面试方向和掌握周期参数，把同一个代码仓转成不同求职场景下的学习资产，这个是从 demo 到应用化的关键。”

## 8) 已知风险与后续优化（加分项）

- 风险：
  - LLM 输出质量受模型波动影响
  - 超大仓库下上下文成本上升
- 优化方向：
  - 增加检索层（按节点拉取局部上下文）
  - 对 `interview_qa` 和 `mastery_report` 增加自动评分与回归测试
  - 增加“失败样本 -> prompt 修正”闭环

## 9) 面试前最后检查清单

- 我能画出完整节点流程
- 我能解释每个核心参数如何影响输出
- 我能讲出至少 2 个工程权衡（单大 prompt vs 多节点、文档生成 vs 学习闭环）
- 我能现场演示 1 次命令并定位输出文件
- 我能说出下一步可扩展方案（检索、评测、质量回归）
