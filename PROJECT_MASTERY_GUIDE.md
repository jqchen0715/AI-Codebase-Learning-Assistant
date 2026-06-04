# 项目掌握指导书

## 1. 项目一句话总结
- 一句话总结：这是一个基于 PocketFlow 的多节点 LLM Workflow，输入 GitHub 仓库或本地目录，自动生成教程、源码阅读路线、面试问答和掌握度报告，把“读不懂项目”变成可执行的学习闭环。
- 简历标题（建议）：AI Codebase Learning Assistant — 多节点 LLM Workflow 的代码仓学习资产生成器

## 2. 项目解决的问题
- 初次接手代码仓时，不知道从哪里读、先看什么。
- 看懂局部实现，但无法串起整体架构与数据流。
- 面试前难以把“读过的代码”转成结构化表达与问答能力。
- 缺少可执行的学习计划和自我掌握度校验。

## 3. 项目整体架构
- 项目定位：AI Agent 应用 + 工具调用型 LLM 应用 + 固定流程 Workflow（非多 Agent、非 RAG、非 Web 后端）。
- 架构概览：
  - CLI 入口解析参数 -> 共享状态 `shared` -> Flow 编排多个 Node -> LLM 生成与校验 -> 输出多类 Markdown 资产。
- 关键特征：
  - 有状态、多步骤的 workflow（不是单个大 prompt）。
  - 输出面向学习与面试的多种产物（教程、阅读路线、Q&A、掌握度报告）。

## 4. 项目运行链路
用户输入
-> 入口文件 `main.py`
-> 核心函数 `main()`
-> FetchRepo（抓取仓库/目录文件）
-> IdentifyAbstractions（LLM 抽象识别 + YAML 校验）
-> AnalyzeRelationships（LLM 生成摘要与关系）
-> OrderChapters（LLM 决定章节顺序）
-> GenerateCodeReadingRoute（LLM 生成阅读路线）
-> GenerateInterviewQA（LLM 生成面试问答）
-> GenerateProjectMasteryReport（LLM 生成掌握度报告）
-> WriteChapters（BatchNode 写章节内容）
-> CombineTutorial（写入 index/route/Q&A/report/chapters）
-> 最终输出到 `output/<project_name>/`

LLM / 工具调用位置：
- LLM：`utils/call_llm.py`（Gemini 或 OpenAI-compatible API）
- 工具/API：GitHub API（`utils/crawl_github_files.py`），本地文件系统（`utils/crawl_local_files.py`）
- 数据库 / 向量库：代码中未看到明确实现

可能失败的环节（常见错误点）：
- 缺少 `GEMINI_API_KEY` 或 `LLM_PROVIDER` 配置（LLM 调用失败）。
- GitHub rate limit 或 token 权限不足（抓取失败）。
- LLM 输出未遵循 YAML 格式导致解析失败（节点重试）。
- 仓库过大导致上下文过长或输出不稳定（无显式分块）。
- 输出目录权限不足或路径非法（写文件失败）。

## 5. 目录结构解析
| 文件/目录 | 作用 | 重要程度 | 为什么重要 | 是否面试高频 |
| --- | --- | --- | --- | --- |
| main.py | CLI 入口、参数解析、初始化 shared | 核心 | 决定输入/配置与运行入口 | 是 |
| flow.py | Flow 编排与节点顺序 | 核心 | 决定执行链路与节点依赖 | 是 |
| nodes.py | 核心节点逻辑、LLM prompt、校验 | 核心 | 业务主流程与质量控制 | 是 |
| utils/call_llm.py | LLM 调用、缓存、日志 | 核心 | 成本/稳定性/可追溯性关键 | 是 |
| utils/crawl_github_files.py | GitHub 抓取与过滤 | 高 | 入口数据源之一 | 是 |
| utils/crawl_local_files.py | 本地目录抓取与过滤 | 高 | 入口数据源之一 | 是 |
| README.md | 项目使用说明 | 中 | 运行和参数理解入口 | 中 |
| requirements.txt | 依赖清单 | 中 | 环境复现与部署 | 中 |
| Dockerfile | Docker 运行入口 | 中 | 演示/部署场景 | 低-中 |
| docs/design.md | 设计说明与流程概览 | 中 | 理解整体设计 | 中 |
| INTERVIEW_GUIDE.md | 面试引导示例文档 | 低 | 参考内容 | 低 |
| output/ | 生成产物 | 低 | 结果查看 | 低 |
| logs/ | LLM 调用日志 | 低 | 排错/回溯 | 低 |
| assets/ | 静态资源 | 低 | 非核心 | 否 |

优先掌握的 5-10 个文件：
1. main.py
2. flow.py
3. nodes.py
4. utils/call_llm.py
5. utils/crawl_github_files.py
6. utils/crawl_local_files.py
7. README.md
8. docs/design.md
9. requirements.txt
10. Dockerfile

推荐阅读顺序：
1. README.md（理解使用场景）
2. main.py（入口与参数）
3. flow.py（执行顺序）
4. nodes.py（主流程）
5. utils/call_llm.py（LLM 接口）
6. utils/crawl_github_files.py / utils/crawl_local_files.py（输入来源）
7. docs/design.md（设计复盘）

## 6. 核心模块拆解

### 模块 1：CLI 输入与 shared 状态
- 解决什么问题：统一用户输入与系统配置，形成可传递的状态。
- 核心代码：`main.py` 中 `main()`。
- 输入：`--repo`/`--dir`、`--language`、`--learner-level` 等参数。
- 输出：`shared` 字典（后续节点共享）。
- 与其他模块连接：作为 Flow 的初始上下文。
- 面试官可能怎么问：为什么要把输入放进 shared，而不是参数层层传递？
- 推荐回答：Flow 是多节点流水线，shared 让节点解耦并具备可插拔能力。

### 模块 2：Workflow 编排
- 解决什么问题：固定顺序执行多个阶段，保证生成结果稳定可控。
- 核心代码：`flow.py` 的 `create_tutorial_flow()`。
- 输入：无（只定义节点连接）。
- 输出：`Flow` 实例。
- 与其他模块连接：驱动 `nodes.py` 的全部节点。
- 面试官可能怎么问：为什么不用单个大 prompt？
- 推荐回答：多节点可分治、可重试、可验证，且便于后续扩展新产物。

### 模块 3：代码抓取与过滤
- 解决什么问题：从 GitHub 或本地目录得到可分析的文件集合。
- 核心代码：`FetchRepo` + `utils/crawl_github_files.py` / `utils/crawl_local_files.py`。
- 输入：repo URL 或本地路径、include/exclude 规则、max_file_size。
- 输出：`shared["files"]`（路径+内容列表）。
- 与其他模块连接：为抽象识别、关系分析提供上下文。
- 面试官可能怎么问：如何避免把无关文件喂给 LLM？
- 推荐回答：用 include/exclude patterns + .gitignore + size limit 过滤。

### 模块 4：抽象识别
- 解决什么问题：从代码库中提炼核心概念与关联文件。
- 核心代码：`IdentifyAbstractions.exec()`。
- 输入：文件内容上下文、学习者等级、语言。
- 输出：`shared["abstractions"]`（name/description/files）。
- 与其他模块连接：驱动关系分析与章节写作。
- 面试官可能怎么问：如何保证 LLM 返回的索引合法？
- 推荐回答：有 YAML 解析与 index 校验，超范围会抛错触发重试。

### 模块 5：关系分析 + 章节排序
- 解决什么问题：生成项目摘要与抽象依赖关系，决定讲解顺序。
- 核心代码：`AnalyzeRelationships.exec()` + `OrderChapters.exec()`。
- 输入：抽象列表、相关代码片段、学习者等级。
- 输出：`shared["relationships"]` 与 `shared["chapter_order"]`。
- 与其他模块连接：阅读路线、面试问答与章节生成都依赖它。
- 面试官可能怎么问：如何避免关系图缺失节点？
- 推荐回答：Prompt 强约束“每个抽象至少出现一次”，并做解析校验。

### 模块 6：学习资产生成
- 解决什么问题：生成阅读路线、面试问答、掌握度报告三类学习资产。
- 核心代码：`GenerateCodeReadingRoute` / `GenerateInterviewQA` / `GenerateProjectMasteryReport`。
- 输入：章节顺序、关系摘要、学习者等级等。
- 输出：`shared["code_reading_route"]` / `shared["interview_qa"]` / `shared["project_mastery_report"]`。
- 与其他模块连接：最终写入输出目录。
- 面试官可能怎么问：为什么面试问答还能“偏置方向”？
- 推荐回答：参数 `interview_focus` 影响 prompt 内容与题型选择。

### 模块 7：章节写作（BatchNode）
- 解决什么问题：按章节顺序生成详细教程内容，避免上下文污染。
- 核心代码：`WriteChapters.exec()`。
- 输入：单个 abstraction + 相关文件内容 + 已写章节摘要。
- 输出：`shared["chapters"]`。
- 与其他模块连接：最后由 CombineTutorial 汇总输出。
- 面试官可能怎么问：BatchNode 的价值是什么？
- 推荐回答：章节天然可分治，BatchNode 支持分批重试与上下文控制。

### 模块 8：输出组装
- 解决什么问题：把所有产物写成最终目录结构并加导航。
- 核心代码：`CombineTutorial.prep/exec()`。
- 输入：summary/relationships/chapters/route/qa/report。
- 输出：`output/<project_name>/` 下的 Markdown 文件。
- 与其他模块连接：最终用户可直接阅读的成品。
- 面试官可能怎么问：如何保证链接一致性？
- 推荐回答：统一通过 `make_chapter_filename` 生成文件名，并保持 order。

### 模块 9：LLM 调用与缓存
- 解决什么问题：统一模型调用、缓存与日志。
- 核心代码：`utils/call_llm.py`。
- 输入：prompt + use_cache。
- 输出：模型响应文本。
- 与其他模块连接：所有生成节点依赖此模块。
- 面试官可能怎么问：缓存策略有什么风险？
- 推荐回答：当前仅按 prompt 缓存，无 TTL 和模型隔离，容易旧结果污染。

## 7. 核心代码讲解

### 核心代码 1：CLI 构建 shared 并启动 Flow
位置：`main.py / main()`

为什么重要：它决定了“输入如何影响输出”，也是 shared 状态的唯一入口。

代码逻辑：解析 CLI 参数 -> 构造 `shared` -> `create_tutorial_flow()` -> `tutorial_flow.run(shared)`。

输入：CLI 参数（repo/dir、learner-level、interview-focus 等）。

输出：驱动整个流程。

可能的面试追问：
1. 为什么 shared 里保存这么多中间产物？
2. 如果加入新产物节点，入口需要改什么？

推荐回答：
- shared 是节点间契约，扩展只需在 shared 增加字段并在节点读取。
- 新节点只需在 flow 里接入，不需要改 CLI。

### 核心代码 2：Flow 顺序编排
位置：`flow.py / create_tutorial_flow()`

为什么重要：定义系统执行链路，是“多节点工作流”的核心体现。

代码逻辑：实例化节点 -> `>>` 串联 -> `Flow(start=fetch_repo)`。

输入：无（结构定义）。

输出：Flow 实例。

可能的面试追问：
1. 为什么 IdentifyAbstractions 需要在 AnalyzeRelationships 之前？
2. 能否并行？

推荐回答：
- 关系分析依赖抽象识别输出，必须先识别抽象。
- 章节生成可批处理，其他阶段依赖强，暂不并行。

### 核心代码 3：抽象识别 + YAML 校验
位置：`nodes.py / IdentifyAbstractions.exec()`

为什么重要：这是从“文件集合”到“概念结构”的第一次质变。

代码逻辑：构造 prompt -> LLM 生成 YAML -> 解析 -> 校验索引合法性 -> 写入 `shared["abstractions"]`。

输入：文件上下文、learner level、language。

输出：结构化抽象列表。

可能的面试追问：
1. 如果 LLM 输出格式错了会怎样？
2. 为什么要用 index 而不是路径字符串？

推荐回答：
- 解析失败会抛异常触发重试，流程有 max_retries。
- index 更稳定、简短，避免长路径引入错误与 prompt 噪声。

### 核心代码 4：关系分析与章节排序
位置：`nodes.py / AnalyzeRelationships.exec()` + `OrderChapters.exec()`

为什么重要：决定项目摘要、抽象间关系、教程讲解顺序。

代码逻辑：关系分析生成 `summary` + `relationships` -> 排序节点输出 `chapter_order`。

输入：抽象列表、相关文件内容。

输出：摘要 + 章节顺序。

可能的面试追问：
1. 如何确保关系覆盖所有抽象？
2. 章节顺序如果错误怎么办？

推荐回答：
- Prompt 强约束 + 校验规则保证每个抽象至少出现一次。
- 顺序可重试；如果仍不理想，可加人工规则或优先级策略。

### 核心代码 5：LLM 调用与缓存
位置：`utils/call_llm.py / call_llm()`

为什么重要：所有生成节点依赖 LLM，稳定性决定产出质量。

代码逻辑：读取 provider -> 选择 Gemini 或 OpenAI-compatible -> 记录日志 -> 缓存 prompt -> 返回响应。

输入：prompt、use_cache。

输出：LLM 响应文本。

可能的面试追问：
1. 缓存的粒度是什么？
2. 如果更换模型，缓存会不会错？

推荐回答：
- 仅按 prompt 缓存，模型/版本未区分，这是风险点，可改进。

### 核心代码 6：GitHub 抓取与过滤
位置：`utils/crawl_github_files.py / crawl_github_files()`

为什么重要：输入质量决定后续 LLM 质量。

代码逻辑：解析 URL -> GitHub API 拉目录/文件 -> include/exclude -> size limit -> 下载内容。

输入：repo_url、token、patterns、max_file_size。

输出：文件字典。

可能的面试追问：
1. GitHub rate limit 怎么处理？
2. 大文件怎么办？

推荐回答：
- 403 rate limit 会等待重试；文件大小限制直接跳过。

### 核心代码 7：章节写作的 BatchNode 设计
位置：`nodes.py / WriteChapters.exec()`

为什么重要：体现“批处理 + 上下文递进”设计。

代码逻辑：每章独立生成 -> 记录前序章节摘要 -> 控制代码块长度 -> 输出章节 Markdown。

输入：抽象信息、相关文件内容、之前章节摘要。

输出：章节内容列表。

可能的面试追问：
1. 为什么要保持 code block < 10 行？
2. 如何避免上下文膨胀？

推荐回答：
- 小块代码便于解释与理解；上下文由章节摘要而非全文避免爆炸。

### 核心代码 8：最终输出组装
位置：`nodes.py / CombineTutorial.prep()`

为什么重要：把所有输出“产品化”，形成可直接使用的学习资产。

代码逻辑：生成 Mermaid 关系图 -> 写 index + route + Q&A + report + chapters。

输入：summary/relationships/chapters 等。

输出：`output/<project_name>/`。

可能的面试追问：
1. Mermaid 标签如何安全化？
2. 如何保证章节链接正确？

推荐回答：
- 标签做了简单替换与长度截断；文件名统一由 `make_chapter_filename` 生成。

## 8. Agent 能力分析
| Agent 能力 | 项目中是否具备 | 具体实现位置 | 成熟度评价 | 如何改进 |
| --- | --- | --- | --- | --- |
| 任务规划 | 部分 | 固定 Flow 顺序 | 中 | 引入动态规划/条件分支 |
| 工具调用 | 部分 | GitHub API、本地文件、LLM 调用 | 中 | 加入可扩展的 Tool Registry |
| 多步骤执行 | 是 | Flow + 多节点 | 高 | 支持并行阶段 |
| 状态管理 | 是 | shared 字典 | 高 | 增加 schema 校验 |
| 短期记忆 | 部分 | 章节摘要串联 | 中 | 引入可控摘要压缩 |
| 结构化输出 | 是 | YAML 输出与校验 | 中-高 | JSON Schema / Pydantic 验证 |
| 失败重试 | 是 | Node max_retries | 中 | 细化错误类型与回退策略 |
| 反思/纠错 | 部分 | 失败重试 | 低 | 增加反思 prompt |
| RAG | 否 | 代码中未看到明确实现 | 低 | 增加检索层与向量库 |
| 评测机制 | 否 | 代码中未看到明确实现 | 低 | 加入 eval 指标与回归测试 |
| 流式输出 | 否 | 代码中未看到明确实现 | 低 | 支持 streaming 输出 |
| 可观测性 | 部分 | LLM 日志、print | 中 | 结构化日志与 trace |

## 9. 技术栈掌握清单
| 技术栈 | 项目中怎么用 | 面试需要掌握到什么程度 | 高频问题 | 推荐学习重点 |
| --- | --- | --- | --- | --- |
| Python | 主体实现 | 熟练 | 参数解析、文件处理 | argparse、上下文管理 |
| PocketFlow | Workflow/Node/BatchNode | 了解原理与使用 | 节点编排、重试机制 | Flow、Node 生命周期 |
| LLM Provider (Gemini/OpenAI-compatible) | `call_llm` | 了解 API 调用与配置 | provider 切换、错误处理 | API key、base URL |
| requests | 调用 GitHub API | 熟练 | rate limit、timeout | 请求重试、错误码处理 |
| GitHub API | 仓库文件抓取 | 了解 | 目录/文件拉取 | 分支/路径解析 |
| GitPython | SSH 仓库抓取 | 了解 | SSH clone 失败 | 认证与临时目录 |
| YAML (pyyaml) | 结构化输出解析 | 熟练 | 解析失败怎么办 | 结构校验 |
| pathspec | 解析 .gitignore | 了解 | 过滤规则优先级 | gitwildmatch |
| dotenv | 环境变量加载 | 了解 | .env 配置 | 运行环境隔离 |
| logging | LLM 日志 | 了解 | 日志落盘 | 结构化日志 |
| Docker | 容器化运行 | 了解 | docker build/run | 环境复制 |
| Mermaid | 关系图输出 | 了解 | diagram 结构 | 标签清洗 |

## 10. 面试官视角审查

### 10.1 项目价值
- 最有价值：把“读代码 + 面试准备”合成一个可执行的学习闭环，不是单纯文档生成。

### 10.2 容易被认为“套壳”的地方
- 大量依赖 LLM 生成文本，核心逻辑偏 prompt 驱动。
- PocketFlow 的流程控制来自框架本身，容易被视为框架能力。

### 10.3 容易被追问穿帮的地方
- 没有评测、RAG、向量库，不能说“知识检索”。
- 缓存策略很简单，无法保证跨模型一致性。
- 抽象与关系依赖 LLM 输出，缺少 deterministic 规则。

### 10.4 可能像 AI 生成但自己没理解的部分
- Prompt 细节、YAML 结构要求、关系图生成逻辑。

### 10.5 框架自带 vs 自己实现
- 框架自带：Flow/Node/BatchNode 基础机制、重试机制。
- 自己实现：抓取逻辑、prompt 设计、共享状态设计、最终输出组装。

### 10.6 简历中应保守表达
- “支持 RAG/检索/向量数据库” -> 代码中未看到明确实现。
- “在线评测/质量监控” -> 未实现。

### 10.7 简历中可大胆写
- “多节点 workflow 编排 + 有状态共享”
- “LLM 产物结构化 + YAML 校验”
- “产出阅读路线/面试问答/掌握度报告”

### 10.8 面试最危险的 10 个问题与回答
1. 你如何保证输出不胡编？
   - 答：限制上下文为抓取文件，并做 YAML 结构与索引校验，失败重试。
2. 为什么不一次性生成全部文档？
   - 答：多节点可分治，可控、可重试，可插拔扩展。
3. 你的缓存策略有什么问题？
   - 答：目前仅按 prompt 缓存，未区分模型/版本，可改进。
4. 如何处理大型仓库的上下文长度？
   - 答：目前靠文件过滤与 size limit，缺少检索层，可改进。
5. LLM 输出格式错误怎么办？
   - 答：解析失败触发重试，但没有更高级纠错。
6. 这个项目算 Agent 吗？
   - 答：是固定流程 workflow，有状态但无动态规划。
7. 为什么不用 RAG？
   - 答：当前没有检索层，后续可加入。
8. BatchNode 的价值是什么？
   - 答：章节天然可分治，降低上下文污染，易重试。
9. 如果 GitHub rate limit？
   - 答：403 会等待 reset 后重试。
10. 如何评估输出质量？
   - 答：目前缺少自动评测，需增加 eval 机制。

## 11. 7 天 / 14 天 / 30 天学习路线

### 7 天速成版
Day 1：
- 看什么：README.md、main.py
- 学什么：CLI 参数、shared 状态
- 改什么：尝试调整 `--learner-level`
- 要能讲清楚什么：入口与参数如何影响输出
- 自测问题：`--interview-focus` 怎么影响内容？

Day 2：
- 看什么：flow.py、nodes.py（整体结构）
- 学什么：Flow/Node/BatchNode
- 改什么：改节点顺序（本地试）
- 要能讲清楚什么：完整执行链路
- 自测问题：为什么需要 `WriteChapters` 批处理？

Day 3：
- 看什么：IdentifyAbstractions、AnalyzeRelationships
- 学什么：YAML 结构化输出与校验
- 改什么：调整 `max_abstractions`
- 要能讲清楚什么：抽象 -> 关系 -> 顺序
- 自测问题：LLM 输出错了如何处理？

Day 4：
- 看什么：GenerateCodeReadingRoute / GenerateInterviewQA
- 学什么：如何把抽象转成学习资产
- 改什么：切换 `interview_focus`
- 要能讲清楚什么：为什么能“面试偏置”
- 自测问题：Q&A 生成的上下文来自哪里？

Day 5：
- 看什么：GenerateProjectMasteryReport
- 学什么：学习路线结构设计
- 改什么：切换 `mastery_horizon`
- 要能讲清楚什么：掌握度报告输出结构
- 自测问题：为什么要固定 3/7/14 天？

Day 6：
- 看什么：utils/call_llm.py
- 学什么：LLM provider 选择与缓存
- 改什么：切换 LLM_PROVIDER
- 要能讲清楚什么：LLM 调用路径
- 自测问题：为什么缓存可能失真？

Day 7：
- 看什么：CombineTutorial + output 产物
- 学什么：输出文件结构
- 改什么：修改 index 模板
- 要能讲清楚什么：最终产物如何被用户使用
- 自测问题：index.md 包含哪些核心导航？

### 14 天巩固版
Day 1-7：同 7 天速成版。
Day 8：
- 看什么：utils/crawl_github_files.py
- 学什么：GitHub API 拉取细节
- 改什么：调整 include/exclude
- 要能讲清楚什么：如何避免无关文件
- 自测问题：rate limit 处理方式？

Day 9：
- 看什么：utils/crawl_local_files.py
- 学什么：.gitignore 过滤
- 改什么：增加排除规则
- 要能讲清楚什么：本地抓取流程
- 自测问题：pathspec 的作用？

Day 10：
- 看什么：WriteChapters.exec 细节
- 学什么：章节摘要递进
- 改什么：调小/调大 code block 限制
- 要能讲清楚什么：如何控制上下文膨胀
- 自测问题：为什么要“前序章节摘要”？

Day 11：
- 看什么：docs/design.md
- 学什么：设计取舍与流程模式
- 改什么：在设计文档补充改进点
- 要能讲清楚什么：为什么是 workflow 不是 agent planning
- 自测问题：workflow 模式的优势？

Day 12：
- 看什么：Dockerfile
- 学什么：容器化运行
- 改什么：加入 env 模板
- 要能讲清楚什么：如何在面试现场演示
- 自测问题：docker run 需要哪些 env？

Day 13：
- 看什么：logs + llm_cache.json
- 学什么：可观测性与缓存策略
- 改什么：增加缓存命中统计
- 要能讲清楚什么：如何定位异常输出
- 自测问题：日志里能看到什么？

Day 14：
- 看什么：输出的 index/route/Q&A/report
- 学什么：如何把产物讲成面试答案
- 改什么：手写一版 Q&A
- 要能讲清楚什么：项目价值与改进方向
- 自测问题：你能否画出数据流图？

### 30 天深入版
Day 1-14：同 14 天巩固版。
Day 15：
- 看什么：所有 prompt 结构
- 学什么：prompt 设计要点
- 改什么：为 YAML 输出加入更强约束
- 要能讲清楚什么：prompt 与稳定性关系
- 自测问题：最容易失败的 prompt 在哪？

Day 16：
- 看什么：call_llm 错误处理
- 学什么：异常分类
- 改什么：增加错误类型与回退策略
- 要能讲清楚什么：如何提升可靠性
- 自测问题：如何区分网络错误与输出错误？

Day 17：
- 看什么：FetchRepo 与过滤策略
- 学什么：上下文裁剪策略
- 改什么：加入文件优先级规则
- 要能讲清楚什么：怎样降低 token 成本
- 自测问题：如何控制上下文大小？

Day 18：
- 看什么：output 产物结构
- 学什么：学习资产可用性
- 改什么：加“练习题”模块
- 要能讲清楚什么：从文档到训练闭环
- 自测问题：如何衡量学习效果？

Day 19：
- 看什么：docs/design.md
- 学什么：系统设计表达
- 改什么：补充权衡分析
- 要能讲清楚什么：设计取舍
- 自测问题：为什么选 Workflow？

Day 20：
- 看什么：nodes.py 的校验逻辑
- 学什么：结构化输出校验
- 改什么：用 Pydantic 替代手写校验
- 要能讲清楚什么：强约束输出的意义
- 自测问题：YAML 校验失败时如何降级？

Day 21：
- 看什么：LLM 日志
- 学什么：输出质量诊断
- 改什么：为每个节点加 metric
- 要能讲清楚什么：如何 debug 生成质量
- 自测问题：哪类错误最常见？

Day 22：
- 看什么：Docker 运行
- 学什么：环境复现
- 改什么：添加 compose 示例
- 要能讲清楚什么：如何快速演示
- 自测问题：Docker 模式有什么限制？

Day 23：
- 看什么：多语言支持
- 学什么：语言适配策略
- 改什么：增加语言映射表
- 要能讲清楚什么：为什么要保留代码标识不翻译
- 自测问题：多语言最大风险？

Day 24：
- 看什么：章节结构
- 学什么：面向不同层级读者
- 改什么：引入不同模板
- 要能讲清楚什么：learner-level 的作用
- 自测问题：初级与高级输出差异？

Day 25：
- 看什么：GenerateInterviewQA
- 学什么：面试题型设计
- 改什么：加入系统性分类
- 要能讲清楚什么：面试偏置怎么实现
- 自测问题：backend 与 rag 的题型差异？

Day 26：
- 看什么：GenerateProjectMasteryReport
- 学什么：学习计划可执行性
- 改什么：加入评分标准
- 要能讲清楚什么：如何衡量掌握度
- 自测问题：如何避免空泛 checklist？

Day 27：
- 看什么：CombineTutorial
- 学什么：最终产物组织方式
- 改什么：增加索引导航与搜索
- 要能讲清楚什么：产物如何被用户消费
- 自测问题：如果章节顺序错了怎么办？

Day 28：
- 看什么：call_llm 缓存
- 学什么：缓存命中策略
- 改什么：加入模型/版本作为 key
- 要能讲清楚什么：缓存对一致性的影响
- 自测问题：如何避免旧缓存污染？

Day 29：
- 看什么：整体流程
- 学什么：端到端数据流
- 改什么：画出完整流程图
- 要能讲清楚什么：端到端调用链
- 自测问题：从 CLI 到最终文件的路径？

Day 30：
- 看什么：项目扩展设想
- 学什么：RAG/评测/检索
- 改什么：提出一版可执行改进
- 要能讲清楚什么：下一步演进路线
- 自测问题：最值得写进简历的改进是什么？

## 12. 面试问答库

### Q1 项目介绍类
- 面试官问题：这个项目到底做什么？
- 考察点：业务定位与端到端理解
- 我的推荐回答：输入代码仓，经过多节点 workflow，输出教程、阅读路线、面试问答和掌握度报告。
- 回答时不要说什么：别说“做了 RAG/向量库”
- 可以延伸讲什么：为什么要拆成多节点

### Q2 技术选型类
- 面试官问题：为什么用 PocketFlow？
- 考察点：框架选择与权衡
- 我的推荐回答：需要可编排、可重试、易扩展的节点流程，PocketFlow 正好提供。
- 回答时不要说什么：避免“随便选的”
- 可以延伸讲什么：BatchNode 的价值

### Q3 Agent 架构类
- 面试官问题：它算 Agent 吗？
- 考察点：Agent 定义理解
- 我的推荐回答：是固定 workflow 的有状态 Agent，不是动态规划型。
- 回答时不要说什么：不要说“多智能体协作”
- 可以延伸讲什么：如何演进为动态规划

### Q4 工具调用类
- 面试官问题：项目里有哪些工具调用？
- 考察点：工具链认知
- 我的推荐回答：GitHub API 抓取、本地目录抓取、LLM 调用。
- 回答时不要说什么：不要说“函数调用”
- 可以延伸讲什么：未来加工具 registry

### Q5 Prompt 设计类
- 面试官问题：如何确保 LLM 输出结构化？
- 考察点：prompt 与验证
- 我的推荐回答：prompt 要求 YAML，代码解析并校验索引。
- 回答时不要说什么：不要说“它自己会懂”
- 可以延伸讲什么：改用 JSON schema

### Q6 RAG 类
- 面试官问题：这个项目有 RAG 吗？
- 考察点：诚实度
- 我的推荐回答：没有，当前是全量上下文；可扩展检索层。
- 回答时不要说什么：不要强行包装
- 可以延伸讲什么：加入向量库的方案

### Q7 后端接口类
- 面试官问题：有服务化接口吗？
- 考察点：系统边界
- 我的推荐回答：当前是 CLI 工具，没有 Web 后端。
- 回答时不要说什么：不要编造 API
- 可以延伸讲什么：可封装为 FastAPI

### Q8 异常处理类
- 面试官问题：LLM 输出错了怎么办？
- 考察点：鲁棒性
- 我的推荐回答：解析失败会抛错，节点重试；更好的做法是增加纠错 prompt。
- 回答时不要说什么：不要说“不会错”
- 可以延伸讲什么：错误分类与回退策略

### Q9 性能优化类
- 面试官问题：大型仓库如何控制成本？
- 考察点：性能与成本意识
- 我的推荐回答：当前靠文件过滤和 size limit，缺少检索层。
- 回答时不要说什么：不要说“无限大都行”
- 可以延伸讲什么：分块+检索

### Q10 项目不足与改进类
- 面试官问题：这个项目最大的短板是什么？
- 考察点：反思能力
- 我的推荐回答：缺少评测与质量回归、缺少检索。
- 回答时不要说什么：不要说“没有短板”
- 可以延伸讲什么：下一步改进路线

## 13. 简历写法

### 保守真实版
项目名称：AI Codebase Learning Assistant
项目描述：基于 PocketFlow 的多节点 LLM Workflow，自动把代码仓转成教程、阅读路线、面试问答与掌握度报告。
技术栈：Python、PocketFlow、Google GenAI、requests、PyYAML、Docker
项目亮点：多节点编排、结构化输出校验、面向学习与面试的多产物输出
简历 bullet：
1. 设计并实现多节点 Workflow，把仓库解析 -> 抽象识别 -> 关系分析 -> 章节生成 -> 输出整合完整串联。
2. 通过 YAML 结构化输出与索引校验，提高 LLM 生成结果的可控性与可重复性。
3. 支持 learner-level 与 interview-focus 参数化，使同一仓库生成不同深度与方向的学习资产。
4. 提供 GitHub/本地双输入方式与 Docker 运行方式，提升演示与复现能力。

### 优化包装版（不夸大）
项目名称：AI Codebase Learning Assistant
项目描述：面向 AI Agent 实习面试的代码仓学习助手，自动生成教程、阅读路线与面试问答，帮助快速形成可表达的项目理解。
技术栈：Python、PocketFlow、Gemini API（或 OpenAI-compatible）、PyYAML、Docker
项目亮点：多阶段流水线 + 结构化校验 + 可配置学习画像
简历 bullet：
1. 构建有状态多节点 workflow，将代码仓自动转化为“阅读路线 + 面试问答 + 掌握度报告”的学习资产。
2. 通过 prompt 约束 + YAML 解析校验，显式控制 LLM 输出格式与文件索引合法性。
3. 基于参数化 learner-level / interview-focus，实现多档深度与面试偏置的产物生成。
4. 集成 GitHub API / 本地目录抓取与缓存日志机制，提升稳定性与可追溯性。

## 14. 项目改进路线

### 低成本改进（1-2 天）
1) 增加模型/版本维度缓存 key
- 改什么：在 `call_llm` 缓存 key 中加入 provider + model
- 为什么改：避免缓存污染
- 涉及文件：utils/call_llm.py
- 需要技术：Python 字典/JSON
- 改完后简历怎么写：优化 LLM 缓存策略，保证多模型结果一致性
- 面试怎么讲：用最小改动提升稳定性

2) 加强 YAML 解析失败的错误提示
- 改什么：捕获解析异常并打印截断响应
- 为什么改：提升可调试性
- 涉及文件：nodes.py
- 需要技术：异常处理
- 简历怎么写：提升 LLM 输出失败的可观测性
- 面试怎么讲：定位问题更快

### 中等改进（3-7 天）
1) 增加简单检索层（基于关键词）
- 改什么：识别抽象/关系时只喂相关文件
- 为什么改：控制上下文成本
- 涉及文件：nodes.py、utils/*
- 需要技术：文本检索、文件索引
- 简历怎么写：引入轻量检索降低 LLM 成本
- 面试怎么讲：如何做粗粒度 RAG

2) 输出质量评测脚本
- 改什么：对生成产物打分或规则检查
- 为什么改：避免回归问题
- 涉及文件：新增 eval 脚本
- 需要技术：文本解析、规则校验
- 简历怎么写：建立生成内容回归评测
- 面试怎么讲：质量控制策略

### 高价值改进（适合写进简历）
1) 引入真正的 RAG/向量库
- 改什么：基于向量索引检索相关文件片段
- 为什么改：大仓库可扩展，提升准确性
- 涉及文件：新增检索模块、节点改写
- 需要技术：向量库、embedding、chunking
- 简历怎么写：构建检索增强的代码仓学习助手
- 面试怎么讲：检索质量与上下文拼接权衡

2) 可视化前端或 API 服务化
- 改什么：封装为 FastAPI + 前端 UI
- 为什么改：更符合应用形态
- 涉及文件：新增服务层
- 需要技术：FastAPI、SSE/前端
- 简历怎么写：提供可交互的学习资产生成服务
- 面试怎么讲：系统边界与部署策略

## 15. 我最应该优先补的短板
1. LLM 输出质量的评测与回归机制（当前缺失）。
2. 大型仓库的上下文控制与检索策略（目前只靠过滤）。
3. 缓存策略与模型版本隔离（当前过于粗糙）。
4. 错误分类与 fallback 机制（现在主要依赖重试）。
5. 服务化/可视化层（当前仅 CLI）。
