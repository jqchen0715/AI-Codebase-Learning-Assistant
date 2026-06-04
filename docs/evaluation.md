# Evaluation & Demo Evidence

This page records the current quantitative evidence for the project. It is intentionally conservative: numbers are derived from files committed in this repository or from the included LLM call log sample, not from untracked claims.

## What Is Already Supported

| Area | Current status | Evidence / scope |
| --- | --- | --- |
| Input source support | GitHub repository URL and local directory | CLI accepts exactly one of `--repo` or `--dir`; GitHub token is optional for public repos and useful for private/rate-limited repos. |
| Validated Demo repositories | 20 repositories/projects | `docs/` contains 20 generated project folders. |
| Generated Demo documents | 184 Markdown files | `docs/*/*.md` total. |
| Generated tutorial chapters | 164 chapter files | `docs/*/*.md` excluding each project `index.md`. |
| Self-analysis Demo | 22 Markdown files | `output/PocketFlow-Tutorial-Codebase-Knowledge#/` contains this project's generated learning assets. |
| Core asset completeness | 4/4 key assets present | `index.md`, `code_reading_route.md`, `interview_qa.md`, `project_mastery_report.md`. |

## Demo Repository Coverage

The included generated examples cover these 20 projects:

| # | Demo project |
| --- | --- |
| 1 | AutoGen Core |
| 2 | Browser Use |
| 3 | Celery |
| 4 | Click |
| 5 | Codex |
| 6 | Crawl4AI |
| 7 | CrewAI |
| 8 | DSPy |
| 9 | FastAPI |
| 10 | Flask |
| 11 | Google A2A |
| 12 | LangGraph |
| 13 | LevelDB |
| 14 | MCP Python SDK |
| 15 | NumPy Core |
| 16 | OpenManus |
| 17 | PocketFlow |
| 18 | Pydantic Core |
| 19 | Requests |
| 20 | SmolaAgents |

## Runtime Sample

| Metric | Current sample |
| --- | --- |
| Log file | `logs/llm_calls_20260512.log` |
| First timestamp | `2026-05-12 13:12:44.926` |
| Last timestamp | `2026-05-12 13:46:19.825` |
| Elapsed generation window | 33m 34s |
| Timestamped LLM log entries | 64 |

Notes:
- This is a representative logged run, not a full benchmark suite.
- Runtime depends heavily on model provider, network latency, cache hits, number of files, and generated chapter count.
- For fair comparisons, run with `--no-cache` and the same model/provider, source repository, include/exclude patterns, and max file size.

## Node Success Rate

The main flow has 9 sequential stages:

1. `FetchRepo`
2. `IdentifyAbstractions`
3. `AnalyzeRelationships`
4. `OrderChapters`
5. `GenerateCodeReadingRoute`
6. `GenerateInterviewQA`
7. `GenerateProjectMasteryReport`
8. `WriteChapters`
9. `CombineTutorial`

For the committed self-analysis Demo, the success proxy is:

| Metric | Result | Acceptance criterion |
| --- | --- | --- |
| Main flow completion | 9/9 stages | Final output directory exists and includes combined assets. |
| Key asset success | 4/4 assets | Four required Markdown assets exist. |
| Chapter asset success | 18 chapter files | Chapter Markdown files exist alongside the required assets. |

This is a file-based completion proxy. The project does not yet persist per-node tracing metadata such as exact start/end time, retry count, or exception type.

## Retry Mechanism Effect

| Aspect | Current implementation |
| --- | --- |
| Configured retry nodes | 7 LLM-dependent nodes |
| Retry policy | `max_retries=5`, `wait=20` seconds |
| Cache behavior | First attempt can use cache; retry attempts bypass cache via `self.cur_retry == 0` checks. |
| What it helps with | Transient model/API failures, invalid YAML, malformed structured outputs, and index validation errors. |
| What is not measured yet | A/B improvement in success rate with retry on vs. retry off. |

Current evidence is implementation-level plus successful Demo completion. To quantify actual retry lift, add structured run telemetry with fields like `node_name`, `attempt`, `success`, `error_type`, `duration_ms`, and `cache_hit`, then compare identical benchmark repos with `max_retries=1` vs. `max_retries=5`.

## Output Quality Evaluation

Current quality evaluation is a manual rubric rather than an automated judge. Use this 5-point rubric for each generated project:

| Dimension | 1 point | 3 points | 5 points |
| --- | --- | --- | --- |
| Structure completeness | Missing required assets | Required assets exist but navigation is uneven | Required assets and chapter links are complete and easy to follow |
| Code anchoring | Mostly generic prose | Some file/function references | Explanations consistently cite real files, functions, and data flow |
| Learning executability | Vague reading advice | Some staged reading tasks | Clear route, checkpoints, and self-tests |
| Interview usefulness | Generic Q&A | Some project-specific answers | Answers include tradeoffs, follow-ups, and defensible boundaries |
| Cross-document consistency | Contradictory claims | Mostly aligned | Index, chapters, route, Q&A, and mastery report reinforce each other |

Suggested release gate:
- Minimum acceptable score: 18/25.
- Strong Demo score: 22/25 or higher.
- Any score below 3 in code anchoring or cross-document consistency should block promotion of that Demo.

Current honest status:
- The repository has strong structural evidence: 20 Demo projects, 184 generated Markdown files, and 4/4 key assets in the self-analysis output.
- It does not yet include automated semantic quality scoring, human-labeled evaluation sets, or regression thresholds in CI.

## Reproducible Metrics Command

Run:

```bash
python tools/collect_metrics.py
```

The script emits JSON with Demo counts, output asset completeness, runtime sample window, retry configuration, and current quality-evaluation status.
