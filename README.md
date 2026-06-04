# AI Codebase Learning Assistant

把 GitHub 仓库或本地代码目录转换成完整学习资产，而不只是教程文档。

输出包括：
- `index.md`：项目总览 + 关系图 + 导航
- `code_reading_route.md`：源码阅读路线（分阶段、分文件）
- `interview_qa.md`：AI Agent 实习面试问答（可按方向偏置）
- `project_mastery_report.md`：项目掌握度报告（入口、数据流、模块职责、扩展点、高频面试题）
- `01_*.md`, `02_*.md`, ...：章节化教程

## What It Solves

- 初看项目不知道从哪里读
- 能看懂局部代码，但抓不到整体数据流
- 面试前无法把“读过的代码”转成可表达的答案
- 缺少可执行的学习计划与掌握度检查

## Quick Start

1. 克隆仓库
```bash
git clone https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge
cd PocketFlow-Tutorial-Codebase-Knowledge
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置模型环境变量（可放到 `.env`）
- 默认 Gemini：`GEMINI_API_KEY`
- 可选自定义 provider：`LLM_PROVIDER`, `<PROVIDER>_MODEL`, `<PROVIDER>_URL`, `<PROVIDER>_API_KEY`
- 可选 GitHub token（提速/私有库）：`GITHUB_TOKEN`

4. 运行最小示例
```bash
python main.py --repo https://github.com/username/repo
```

## Output Structure

默认输出目录：`./output/<project_name>/`

- `index.md`
- `code_reading_route.md`
- `interview_qa.md`
- `project_mastery_report.md`
- `01_<chapter>.md`, `02_<chapter>.md`, ...

## Full CLI

```bash
python main.py \
  (--repo <github_url> | --dir <local_dir>) \
  [-n <project_name>] \
  [-t <github_token>] \
  [-o <output_dir>] \
  [-i <include_patterns...>] \
  [-e <exclude_patterns...>] \
  [-s <max_file_size>] \
  [--language <language>] \
  [--learner-level <beginner|intermediate|advanced>] \
  [--interview-focus <general|backend|agent-framework|rag|llm-infra|eval>] \
  [--mastery-horizon <3d|7d|14d>] \
  [--max-abstractions <int>] \
  [--no-cache]
```

## Parameter Reference

- `--repo` / `--dir`：二选一，GitHub 仓库地址或本地目录
- `-n, --name`：项目名（不传会自动推断）
- `-t, --token`：GitHub token（也可用 `GITHUB_TOKEN`）
- `-o, --output`：输出根目录（默认 `output`）
- `-i, --include`：包含文件模式（如 `*.py` `*.ts`）
- `-e, --exclude`：排除文件模式（如 `tests/*` `docs/*`）
- `-s, --max-size`：单文件最大字节数（默认 `100000`）
- `--language`：生成语言（默认 `english`）
- `--learner-level`：讲解深度
  - `beginner`：更强调概念、类比、入门路径
  - `intermediate`：更强调职责、协作、改动点
  - `advanced`：更强调不变量、扩展点、性能与权衡
- `--interview-focus`：面试问答偏置方向
  - `general`：均衡
  - `backend`：可靠性、边界、并发、容错
  - `agent-framework`：编排、状态传递、工具调用
  - `rag`：检索链路、索引/召回权衡、grounding
  - `llm-infra`：provider 抽象、缓存重试、成本时延质量权衡
  - `eval`：评测指标、回归防护、质量诊断
- `--mastery-horizon`：掌握度报告学习周期
  - `3d`：短冲刺
  - `7d`：默认平衡
  - `14d`：深入掌握
- `--max-abstractions`：抽象数量上限（默认 `10`）
- `--no-cache`：关闭 LLM 缓存

## Common Run Recipes

1. 生成中文 + 中级讲解 + 后端面试偏置 + 7天掌握计划
```bash
python main.py \
  --repo https://github.com/username/repo \
  --language Chinese \
  --learner-level intermediate \
  --interview-focus backend \
  --mastery-horizon 7d
```

2. 针对 Agent 框架实习面试
```bash
python main.py \
  --repo https://github.com/username/repo \
  --interview-focus agent-framework \
  --mastery-horizon 14d
```

3. 分析本地目录并限制文件范围
```bash
python main.py \
  --dir /path/to/codebase \
  --include "*.py" "*.md" \
  --exclude "tests/*" "docs/*" \
  --learner-level beginner
```

## Docker

1. 构建镜像
```bash
docker build -t pocketflow-app .
```

2. 运行（分析 GitHub 仓库）
```bash
docker run -it --rm \
  -e GEMINI_API_KEY="YOUR_GEMINI_API_KEY" \
  -e GITHUB_TOKEN="YOUR_GITHUB_TOKEN" \
  -v "$(pwd)/output_tutorials":/app/output \
  pocketflow-app \
  --repo https://github.com/username/repo \
  --interview-focus backend \
  --mastery-horizon 7d
```

3. 运行（分析本地代码目录）
```bash
docker run -it --rm \
  -e GEMINI_API_KEY="YOUR_GEMINI_API_KEY" \
  -v "/path/to/your/local_codebase":/app/code_to_analyze \
  -v "$(pwd)/output_tutorials":/app/output \
  pocketflow-app \
  --dir /app/code_to_analyze
```

## Notes

- `docs/design.md` 记录了流程和节点设计。
- 模型调用逻辑在 `utils/call_llm.py`。
- 若你希望把输出进一步变成“每日训练模式”，可以在后续扩展 `project_mastery_report.md` 的任务模板与打分规则。
