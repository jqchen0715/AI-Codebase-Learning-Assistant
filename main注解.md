``` python

import dotenv
import os
#用来写命令行参数解析，也就是说，这个脚本是通过命令行运行的：python main.py --repo https://github.com/xxx/xxx --language chinese
import argparse
# Import the function that creates the flow
from flow import create_tutorial_flow

dotenv.load_dotenv()

‘’‘
这是默认包含的文件类型。
意思是：如果用户没有手动指定 --include，程序默认会读取这些文件。
‘’‘
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
    "*Makefile", "*.yaml", "*.yml",
}
‘’‘
这是默认排除的文件/目录。
也就是说，就算某些文件符合 include 规则，只要它也符合 exclude 规则，就会被跳过。
’‘’
DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
    "*docs/*",
    "*venv/*",
    "*.venv/*",
    "*test*",
    "*tests/*",
    "*examples/*",
    "v1/*",
    "*dist/*",
    "*build/*",
    "*experimental/*",
    "*deprecated/*",
    "*misc/*",
    "*legacy/*",
    ".git/*", ".github/*", ".next/*", ".vscode/*",
    "*obj/*",
    "*bin/*",
    "*node_modules/*",
    "*.log"
}
```学习水平设置，面向不同水平的学习者提供不同深度的解释。后面命令行参数里会用到：--learner-level:```
LEARNER_LEVELS = ("beginner", "intermediate", "advanced")
```面试聚焦的设置，针对不同的面试重点生成相应的面试问答。后面命令行参数里会用到：--interview-focus:```
INTERVIEW_FOCUS_CHOICES = (
    "general",
    "backend",
    "agent-framework",
    "rag",
    "llm-infra",
    "eval",
)
```掌握设置，定义了学习计划的时间范围，帮助生成适合短期或长期学习的项目掌握报告。后面命令行参数里会用到：--mastery-horizon:```
MASTERY_HORIZON_CHOICES = ("3d", "7d", "14d")

# --- Main Function ---
#创建一个命令行参数解析器，让用户可以通过命令行告诉程序“我要分析哪个代码仓库/本地目录”
def main():
   #解析用户在命令行里输入的参数。
    parser = argparse.ArgumentParser(description="Generate a tutorial for a GitHub codebase or local directory.")

    # 创建互斥参数组，确保用户只能提供 repo 或 dir 其中一个
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo", help="URL of the public GitHub repository.")
    source_group.add_argument("--dir", help="Path to local directory.")
    #这几行都是在给命令行工具添加可选参数。也就是说，用户运行 main.py 时，可以通过这些参数控制项目名称、GitHub token、输出目录、文件筛选规则和文件大小限制。
    parser.add_argument("-n", "--name", help="Project name (optional, derived from repo/directory if omitted).") #指定项目名：python main.py --dir ./IC-Expert-agent --name IC智能问答系统
    parser.add_argument("-t", "--token", help="GitHub personal access token (optional, reads from GITHUB_TOKEN env var if not provided).")#传入GitHub个人访问令牌，开放的仓库不需要
    parser.add_argument("-o", "--output", default="output", help="Base directory for output (default: ./output).")#指定输出目录
    parser.add_argument("-i", "--include", nargs="+", help="Include file patterns (e.g. '*.py' '*.js'). Defaults to common code files if not specified.")#指定包含的文件类型
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns (e.g. 'tests/*' 'docs/*'). Defaults to test/build directories if not specified.")#指定排除的文件类型或目录
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes (default: 100000, about 100KB).")#指定分析的文件大小限制，默认10万字节（约100KB），超过这个大小的文件将被跳过，以避免处理过大的文件导致性能问题。
    # Add language parameter for multi-language support
    parser.add_argument("--language", default="chinese", help="Language for the generated tutorial (default: chinese)")#控制生成教程使用什么语言，默认中文
    # Add learner level parameter for audience-aware explanations
    parser.add_argument(
        "--learner-level",
        type=str.lower,
        choices=LEARNER_LEVELS,
        default="beginner",
        help="Learner level for explanations: beginner, intermediate, or advanced (default: beginner)",
    ) #控制生成的教程面向什么水平的学习者，默认初级（beginner）。不同水平的学习者会得到不同深度和复杂度的解释，确保内容既不过于简单也不过于复杂
    parser.add_argument(
        "--interview-focus",
        type=str.lower,
        choices=INTERVIEW_FOCUS_CHOICES,
        default="general",
        help="Interview focus for interview_qa generation: general, backend, agent-framework, rag, llm-infra, eval (default: general)",
    )#控制生成的面试问答聚焦于哪个领域，默认是 general（通用）。不同的面试重点会生成针对性的问答内容，帮助求职者更好地准备相关领域的面试。
    parser.add_argument(
        "--mastery-horizon",
        type=str.lower,
        choices=MASTERY_HORIZON_CHOICES,
        default="7d",
        help="Learning plan horizon for project_mastery_report: 3d, 7d, 14d (default: 7d)",
    )#控制生成的项目掌握报告适合多长时间的学习计划，默认是7天（7d）。不同的掌握时间范围会影响学习建议的深度和广度，帮助学习者制定合理的学习计划。
    # Add use_cache parameter to control LLM caching
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM response caching (default: caching enabled)")#决定是否禁用LLM响应缓存，默认是启用缓存。启用缓存可以加快处理速度和减少API调用次数，但在调试或需要最新响应时可以选择禁用。
    # Add max_abstraction_num parameter to control the number of abstractions
    parser.add_argument("--max-abstractions", type=int, default=10, help="Maximum number of abstractions to identify (default: 10)")#最多提炼多少个抽象概念

    args = parser.parse_args()#式解析用户在命令行里输入的参数。

    # Get GitHub token from argument or environment variable if using repo
    github_token = None
    if args.repo:
        github_token = args.token or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("Warning: No GitHub token provided. You might hit rate limits for public repositories.")

    # Initialize the shared dictionary with inputs
    ‘’‘
    前面的 argparse 负责从命令行接收参数；
    后面的 flow 负责真正分析代码、生成教程；
    中间就靠 shared 把信息传过去。
    ’’‘
    shared = {
        "repo_url": args.repo,
        "local_dir": args.dir,
        "project_name": args.name, # Can be None, FetchRepo will derive it
        "github_token": github_token,
        "output_dir": args.output, # Base directory for CombineTutorial output

        # Add include/exclude patterns and max file size
        ‘’‘这三行是在继续填充 shared 字典，作用是把文件筛选规则和文件大小限制传给后面的代码库分析流程。’‘’
        "include_patterns": set(args.include) if args.include else DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": set(args.exclude) if args.exclude else DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": args.max_size,

        # Add language for multi-language support
        "language": args.language,

        # Add learner level for audience-aware explanations
        "learner_level": args.learner_level,

        # Add interview focus for interview Q&A generation
        "interview_focus": args.interview_focus,

        # Add mastery horizon for project mastery report
        "mastery_horizon": args.mastery_horizon,
        
        # Add use_cache flag (inverse of no-cache flag)
        "use_cache": not args.no_cache,
        
        # Add max_abstraction_num parameter
        "max_abstraction_num": args.max_abstractions,

        # Outputs will be populated by the nodes
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "code_reading_route": "",
        "interview_qa": "",
        "project_mastery_report": "",
        "chapters": [],
        "final_output_dir": None
    }

    # Display starting message with repository/directory and language
    print(f"Starting tutorial generation for: {args.repo or args.dir} in {args.language.capitalize()} language")
    print(f"Learner level: {args.learner_level}")
    print(f"Interview focus: {args.interview_focus}")
    print(f"Mastery horizon: {args.mastery_horizon}")
    print(f"LLM caching: {'Disabled' if args.no_cache else 'Enabled'}")

    # Create the flow instance
    ‘’‘创建一个完整的代码库教程生成流程。’‘’
    tutorial_flow = create_tutorial_flow()

    # Run the flow
    ‘’‘这行才是真正开始执行流程。
它把前面构造好的 shared 字典传进去。
也就是说，shared 里面的这些信息都会被后续节点使用：’‘’
    tutorial_flow.run(shared)

if __name__ == "__main__":
    main()
