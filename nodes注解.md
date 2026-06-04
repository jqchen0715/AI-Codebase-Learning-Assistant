``` python
import os
import re
import yaml
from pocketflow import Node, BatchNode
from utils.crawl_github_files import crawl_github_files
from utils.call_llm import call_llm
from utils.crawl_local_files import crawl_local_files


# Helper to get content for specific file indices
#作用是：根据文件编号 indices，从全部文件列表 files_data 里取出指定文件的内容，并整理成一个字典，方便后面喂给 LLM。
def get_content_for_indices(files_data, indices): #files_data：全部文件数据 indices：想要提取的文件编号列表
    #创建一个空字典，用来保存最终结果。
    content_map = {}
    for i in indices: #遍历用户想要取出的文件编号。
        #放进字典里面的内容为：
        {
    "0 # main.py": "...main.py 的代码内容...",
    "2 # nodes.py": "...nodes.py 的代码内容..."
        }
        if 0 <= i < len(files_data):
            path, content = files_data[i]
            content_map[f"{i} # {path}"] = (
                content  # Use index + path as key for context
            )
    return content_map

#把一个任意名称转换成适合当文件名使用的安全字符串。
def make_safe_filename(name):
    return "".join(c if c.isalnum() else "_" for c in name).lower()

#根据章节编号和章节名，生成一个标准的 Markdown 文件名。
def make_chapter_filename(chapter_num, chapter_name):
    return f"{chapter_num:02d}_{make_safe_filename(chapter_name)}.md"


LEARNER_LEVEL_PROFILES = {
    "beginner": {
        "label": "beginner",
        "abstraction": (
            "Assume the reader is new to this codebase and may be new to the "
            "frameworks involved. Use plain language, define jargon before "
            "using it, include one simple analogy where helpful, and focus on "
            "what problem each abstraction solves before implementation details."
        ),
        "summary": (
            "Write for a beginner: explain the project's purpose in simple "
            "terms, name the main moving parts, and avoid assuming prior "
            "architecture knowledge."
        ),
        "chapter": (
            "Make the chapter very approachable. Start from a concrete use "
            "case, explain jargon before using it, use simple analogies and "
            "small examples, keep code snippets minimal, and prefer step-by-step "
            "walkthroughs over dense implementation detail."
        ),
        "chapter_goal": "a very beginner-friendly",
        "closing_tone": "welcoming and easy for a newcomer to understand",
    },
    "intermediate": {
        "label": "intermediate",
        "abstraction": (
            "Assume the reader is comfortable reading code and knows common "
            "framework concepts, but is new to this repository. Explain "
            "responsibilities, data flow, collaboration points, and important "
            "design choices. Use analogies sparingly and only when they clarify "
            "a non-obvious idea."
        ),
        "summary": (
            "Write for an intermediate developer: emphasize architecture, data "
            "flow, component responsibilities, and where a maintainer would look "
            "to change behavior."
        ),
        "chapter": (
            "Write for a developer who can read the code but needs repository "
            "orientation. Cover the practical role of the abstraction, its API "
            "or lifecycle, how it collaborates with adjacent pieces, key design "
            "tradeoffs, and enough internal detail to support confident changes."
        ),
        "chapter_goal": "an intermediate-level",
        "closing_tone": "clear, practical, and useful for a developer onboarding to the repository",
    },
    "advanced": {
        "label": "advanced",
        "abstraction": (
            "Assume the reader is an experienced engineer. Be concise and "
            "technical. Focus on architecture, invariants, extension points, "
            "failure modes, performance implications, and non-obvious tradeoffs. "
            "Avoid basic analogies unless they reveal structure more precisely."
        ),
        "summary": (
            "Write for an advanced engineer: summarize the architecture, major "
            "control/data flows, key tradeoffs, invariants, extension points, "
            "and operational or performance concerns."
        ),
        "chapter": (
            "Write for an experienced engineer. Prioritize concise technical "
            "depth: architecture, invariants, call paths, extension points, "
            "error handling, performance implications, and tradeoffs. Avoid "
            "over-explaining basic programming concepts."
        ),
        "chapter_goal": "an advanced-level",
        "closing_tone": "precise, technical, and useful for an experienced maintainer",
    },
}

INTERVIEW_FOCUS_PROFILES = {
    "general": {
        "label": "general AI Agent internship",
        "guidance": (
            "Balance architecture understanding, coding implementation, debugging, "
            "and practical tradeoff discussion."
        ),
    },
    "backend": {
        "label": "backend",
        "guidance": (
            "Prioritize API boundaries, reliability, error handling, concurrency, "
            "data flow, and production-oriented engineering decisions."
        ),
    },
    "agent-framework": {
        "label": "agent framework",
        "guidance": (
            "Prioritize agent workflow orchestration, node boundaries, state passing, "
            "tool-calling patterns, and extension points for new capabilities."
        ),
    },
    "rag": {
        "label": "retrieval-augmented generation",
        "guidance": (
            "Prioritize retrieval pipeline quality, chunking/indexing tradeoffs, "
            "grounding quality, context assembly, and failure/precision-recall risks."
        ),
    },
    "llm-infra": {
        "label": "LLM infrastructure",
        "guidance": (
            "Prioritize model/provider abstraction, caching, retries, latency-cost-quality "
            "tradeoffs, prompt robustness, and operational reliability concerns."
        ),
    },
    "eval": {
        "label": "evaluation and quality",
        "guidance": (
            "Prioritize measurable quality criteria, testability, offline/online evaluation "
            "strategy, regression prevention, and diagnosis of weak outputs."
        ),
    },
}

MASTERY_HORIZON_DAYS = {
    "3d": 3,
    "7d": 7,
    "14d": 14,
}


def normalize_learner_level(learner_level):
    level = str(learner_level or "beginner").strip().lower()
    if level not in LEARNER_LEVEL_PROFILES:
        valid_levels = ", ".join(LEARNER_LEVEL_PROFILES)
        raise ValueError(
            f"Invalid learner_level '{learner_level}'. Expected one of: {valid_levels}"
        )
    return level


def get_learner_level_profile(learner_level):
    level = normalize_learner_level(learner_level)
    return LEARNER_LEVEL_PROFILES[level]


def normalize_interview_focus(interview_focus):
    focus = str(interview_focus or "general").strip().lower()
    if focus not in INTERVIEW_FOCUS_PROFILES:
        valid_focuses = ", ".join(INTERVIEW_FOCUS_PROFILES)
        raise ValueError(
            f"Invalid interview_focus '{interview_focus}'. Expected one of: {valid_focuses}"
        )
    return focus


def get_interview_focus_profile(interview_focus):
    focus = normalize_interview_focus(interview_focus)
    return INTERVIEW_FOCUS_PROFILES[focus]


def normalize_mastery_horizon(mastery_horizon):
    horizon = str(mastery_horizon or "7d").strip().lower()
    if horizon not in MASTERY_HORIZON_DAYS:
        valid_horizons = ", ".join(MASTERY_HORIZON_DAYS)
        raise ValueError(
            f"Invalid mastery_horizon '{mastery_horizon}'. Expected one of: {valid_horizons}"
        )
    return horizon


class FetchRepo(Node):
    def prep(self, shared):
        repo_url = shared.get("repo_url")
        local_dir = shared.get("local_dir")
        project_name = shared.get("project_name")

        if not project_name:
            # Basic name derivation from URL or directory
            if repo_url:
                project_name = repo_url.split("/")[-1].replace(".git", "")
            else:
                project_name = os.path.basename(os.path.abspath(local_dir))
            shared["project_name"] = project_name

        # Get file patterns directly from shared
        include_patterns = shared["include_patterns"]
        exclude_patterns = shared["exclude_patterns"]
        max_file_size = shared["max_file_size"]

        return {
            "repo_url": repo_url,
            "local_dir": local_dir,
            "token": shared.get("github_token"),
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "max_file_size": max_file_size,
            "use_relative_paths": True,
        }

    def exec(self, prep_res):
        if prep_res["repo_url"]:
            print(f"Crawling repository: {prep_res['repo_url']}...")
            result = crawl_github_files(
                repo_url=prep_res["repo_url"],
                token=prep_res["token"],
                include_patterns=prep_res["include_patterns"],
                exclude_patterns=prep_res["exclude_patterns"],
                max_file_size=prep_res["max_file_size"],
                use_relative_paths=prep_res["use_relative_paths"],
            )
        else:
            print(f"Crawling directory: {prep_res['local_dir']}...")

            result = crawl_local_files(
                directory=prep_res["local_dir"],
                include_patterns=prep_res["include_patterns"],
                exclude_patterns=prep_res["exclude_patterns"],
                max_file_size=prep_res["max_file_size"],
                use_relative_paths=prep_res["use_relative_paths"]
            )

        # Convert dict to list of tuples: [(path, content), ...]
        files_list = list(result.get("files", {}).items())
        if len(files_list) == 0:
            raise (ValueError("Failed to fetch files"))
        print(f"Fetched {len(files_list)} files.")
        return files_list

    def post(self, shared, prep_res, exec_res):
        shared["files"] = exec_res  # List of (path, content) tuples


class IdentifyAbstractions(Node):
    def prep(self, shared):
        files_data = shared["files"]
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True
        max_abstraction_num = shared.get("max_abstraction_num", 10)  # Get max_abstraction_num, default to 10

        # Helper to create context from files, respecting limits (basic example)
        def create_llm_context(files_data):
            context = ""
            file_info = []  # Store tuples of (index, path)
            for i, (path, content) in enumerate(files_data):
                entry = f"--- File Index {i}: {path} ---\n{content}\n\n"
                context += entry
                file_info.append((i, path))

            return context, file_info  # file_info is list of (index, path)

        context, file_info = create_llm_context(files_data)
        # Format file info for the prompt (comment is just a hint for LLM)
        file_listing_for_prompt = "\n".join(
            [f"- {idx} # {path}" for idx, path in file_info]
        )
        return (
            context,
            file_listing_for_prompt,
            len(files_data),
            project_name,
            language,
            learner_level,
            use_cache,
            max_abstraction_num,
        )  # Return all parameters

    def exec(self, prep_res):
        (
            context,
            file_listing_for_prompt,
            file_count,
            project_name,
            language,
            learner_level,
            use_cache,
            max_abstraction_num,
        ) = prep_res  # Unpack all parameters
        print(f"Identifying abstractions using LLM...")
        learner_profile = get_learner_level_profile(learner_level)

        # Add language instruction and hints only if not English
        language_instruction = ""
        name_lang_hint = ""
        desc_lang_hint = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `name` and `description` for each abstraction in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            # Keep specific hints here as name/description are primary targets
            name_lang_hint = f" (value in {language.capitalize()})"
            desc_lang_hint = f" (value in {language.capitalize()})"

        prompt = f"""
For the project `{project_name}`:

Codebase Context:
{context}

{language_instruction}Analyze the codebase context.
Identify the top 5-{max_abstraction_num} core most important abstractions to help a {learner_profile["label"]} learner understand this codebase.

Learner level guidance:
{learner_profile["abstraction"]}

For each abstraction, provide:
1. A concise `name`{name_lang_hint}.
2. A `description` tailored to a {learner_profile["label"]} learner, in around 100 words{desc_lang_hint}.
3. A list of relevant `file_indices` (integers) using the format `idx # path/comment`.

List of file indices and paths present in the context:
{file_listing_for_prompt}

Format the output as a YAML list of dictionaries:

```yaml
- name: |
    Query Processing{name_lang_hint}
  description: |
    Explains what the abstraction does.
    It's like a central dispatcher routing requests.{desc_lang_hint}
  file_indices:
    - 0 # path/to/file1.py
    - 3 # path/to/related.py
- name: |
    Query Optimization{name_lang_hint}
  description: |
    Another core concept, similar to a blueprint for objects.{desc_lang_hint}
  file_indices:
    - 5 # path/to/another.js
# ... up to {max_abstraction_num} abstractions
```"""
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))  # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        abstractions = yaml.safe_load(yaml_str)

        if not isinstance(abstractions, list):
            raise ValueError("LLM Output is not a list")

        validated_abstractions = []
        for item in abstractions:
            if not isinstance(item, dict) or not all(
                k in item for k in ["name", "description", "file_indices"]
            ):
                raise ValueError(f"Missing keys in abstraction item: {item}")
            if not isinstance(item["name"], str):
                raise ValueError(f"Name is not a string in item: {item}")
            if not isinstance(item["description"], str):
                raise ValueError(f"Description is not a string in item: {item}")
            if not isinstance(item["file_indices"], list):
                raise ValueError(f"file_indices is not a list in item: {item}")

            # Validate indices
            validated_indices = []
            for idx_entry in item["file_indices"]:
                try:
                    if isinstance(idx_entry, int):
                        idx = idx_entry
                    elif isinstance(idx_entry, str) and "#" in idx_entry:
                        idx = int(idx_entry.split("#")[0].strip())
                    else:
                        idx = int(str(idx_entry).strip())

                    if not (0 <= idx < file_count):
                        raise ValueError(
                            f"Invalid file index {idx} found in item {item['name']}. Max index is {file_count - 1}."
                        )
                    validated_indices.append(idx)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Could not parse index from entry: {idx_entry} in item {item['name']}"
                    )

            item["files"] = sorted(list(set(validated_indices)))
            # Store only the required fields
            validated_abstractions.append(
                {
                    "name": item["name"],  # Potentially translated name
                    "description": item[
                        "description"
                    ],  # Potentially translated description
                    "files": item["files"],
                }
            )

        print(f"Identified {len(validated_abstractions)} abstractions.")
        return validated_abstractions

    def post(self, shared, prep_res, exec_res):
        shared["abstractions"] = (
            exec_res  # List of {"name": str, "description": str, "files": [int]}
        )


class AnalyzeRelationships(Node):
    def prep(self, shared):
        abstractions = shared[
            "abstractions"
        ]  # Now contains 'files' list of indices, name/description potentially translated
        files_data = shared["files"]
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Get the actual number of abstractions directly
        num_abstractions = len(abstractions)

        # Create context with abstraction names, indices, descriptions, and relevant file snippets
        context = "Identified Abstractions:\\n"
        all_relevant_indices = set()
        abstraction_info_for_prompt = []
        for i, abstr in enumerate(abstractions):
            # Use 'files' which contains indices directly
            file_indices_str = ", ".join(map(str, abstr["files"]))
            # Abstraction name and description might be translated already
            info_line = f"- Index {i}: {abstr['name']} (Relevant file indices: [{file_indices_str}])\\n  Description: {abstr['description']}"
            context += info_line + "\\n"
            abstraction_info_for_prompt.append(
                f"{i} # {abstr['name']}"
            )  # Use potentially translated name here too
            all_relevant_indices.update(abstr["files"])

        context += "\\nRelevant File Snippets (Referenced by Index and Path):\\n"
        # Get content for relevant files using helper
        relevant_files_content_map = get_content_for_indices(
            files_data, sorted(list(all_relevant_indices))
        )
        # Format file content for context
        file_context_str = "\\n\\n".join(
            f"--- File: {idx_path} ---\\n{content}"
            for idx_path, content in relevant_files_content_map.items()
        )
        context += file_context_str

        return (
            context,
            "\n".join(abstraction_info_for_prompt),
            num_abstractions, # Pass the actual count
            project_name,
            language,
            learner_level,
            use_cache,
        )  # Return use_cache

    def exec(self, prep_res):
        (
            context,
            abstraction_listing,
            num_abstractions, # Receive the actual count
            project_name,
            language,
            learner_level,
            use_cache,
         ) = prep_res  # Unpack use_cache
        print(f"Analyzing relationships using LLM...")
        learner_profile = get_learner_level_profile(learner_level)

        # Add language instruction and hints only if not English
        language_instruction = ""
        lang_hint = ""
        list_lang_note = ""
        if language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate the `summary` and relationship `label` fields in **{language.capitalize()}** language. Do NOT use English for these fields.\n\n"
            lang_hint = f" (in {language.capitalize()})"
            list_lang_note = f" (Names might be in {language.capitalize()})"  # Note for the input list

        prompt = f"""
Based on the following abstractions and relevant code snippets from the project `{project_name}`:

List of Abstraction Indices and Names{list_lang_note}:
{abstraction_listing}

Context (Abstractions, Descriptions, Code):
{context}

Learner level guidance:
{learner_profile["summary"]}

{language_instruction}Please provide:
1. A high-level `summary` of the project's main purpose and functionality tailored to a {learner_profile["label"]} learner{lang_hint}. Use markdown formatting with **bold** and *italic* text to highlight important concepts.
2. A list (`relationships`) describing the key interactions between these abstractions. For each relationship, specify:
    - `from_abstraction`: Index of the source abstraction (e.g., `0 # AbstractionName1`)
    - `to_abstraction`: Index of the target abstraction (e.g., `1 # AbstractionName2`)
    - `label`: A brief label for the interaction **in just a few words**{lang_hint} (e.g., "Manages", "Inherits", "Uses").
    Ideally the relationship should be backed by one abstraction calling or passing parameters to another.
    Simplify the relationship and exclude those non-important ones.

IMPORTANT: Make sure EVERY abstraction is involved in at least ONE relationship (either as source or target). Each abstraction index must appear at least once across all relationships.

Format the output as YAML:

```yaml
summary: |
  A brief, simple explanation of the project{lang_hint}.
  Can span multiple lines with **bold** and *italic* for emphasis.
relationships:
  - from_abstraction: 0 # AbstractionName1
    to_abstraction: 1 # AbstractionName2
    label: "Manages"{lang_hint}
  - from_abstraction: 2 # AbstractionName3
    to_abstraction: 0 # AbstractionName1
    label: "Provides config"{lang_hint}
  # ... other relationships
```

Now, provide the YAML output:
"""
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0)) # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        relationships_data = yaml.safe_load(yaml_str)

        if not isinstance(relationships_data, dict) or not all(
            k in relationships_data for k in ["summary", "relationships"]
        ):
            raise ValueError(
                "LLM output is not a dict or missing keys ('summary', 'relationships')"
            )
        if not isinstance(relationships_data["summary"], str):
            raise ValueError("summary is not a string")
        if not isinstance(relationships_data["relationships"], list):
            raise ValueError("relationships is not a list")

        # Validate relationships structure
        validated_relationships = []
        for rel in relationships_data["relationships"]:
            # Check for 'label' key
            if not isinstance(rel, dict) or not all(
                k in rel for k in ["from_abstraction", "to_abstraction", "label"]
            ):
                raise ValueError(
                    f"Missing keys (expected from_abstraction, to_abstraction, label) in relationship item: {rel}"
                )
            # Validate 'label' is a string
            if not isinstance(rel["label"], str):
                raise ValueError(f"Relationship label is not a string: {rel}")

            # Validate indices
            try:
                from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
                to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
                if not (
                    0 <= from_idx < num_abstractions and 0 <= to_idx < num_abstractions
                ):
                    raise ValueError(
                        f"Invalid index in relationship: from={from_idx}, to={to_idx}. Max index is {num_abstractions-1}."
                    )
                validated_relationships.append(
                    {
                        "from": from_idx,
                        "to": to_idx,
                        "label": rel["label"],  # Potentially translated label
                    }
                )
            except (ValueError, TypeError):
                raise ValueError(f"Could not parse indices from relationship: {rel}")

        print("Generated project summary and relationship details.")
        return {
            "summary": relationships_data["summary"],  # Potentially translated summary
            "details": validated_relationships,  # Store validated, index-based relationships with potentially translated labels
        }

    def post(self, shared, prep_res, exec_res):
        # Structure is now {"summary": str, "details": [{"from": int, "to": int, "label": str}]}
        # Summary and label might be translated
        shared["relationships"] = exec_res


class OrderChapters(Node):
    def prep(self, shared):
        abstractions = shared["abstractions"]  # Name/description might be translated
        relationships = shared["relationships"]  # Summary/label might be translated
        project_name = shared["project_name"]  # Get project name
        language = shared.get("language", "english")  # Get language
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Prepare context for the LLM
        abstraction_info_for_prompt = []
        for i, a in enumerate(abstractions):
            abstraction_info_for_prompt.append(
                f"- {i} # {a['name']}"
            )  # Use potentially translated name
        abstraction_listing = "\n".join(abstraction_info_for_prompt)

        # Use potentially translated summary and labels
        summary_note = ""
        if language.lower() != "english":
            summary_note = (
                f" (Note: Project Summary might be in {language.capitalize()})"
            )

        context = f"Project Summary{summary_note}:\n{relationships['summary']}\n\n"
        context += "Relationships (Indices refer to abstractions above):\n"
        for rel in relationships["details"]:
            from_name = abstractions[rel["from"]]["name"]
            to_name = abstractions[rel["to"]]["name"]
            # Use potentially translated 'label'
            context += f"- From {rel['from']} ({from_name}) to {rel['to']} ({to_name}): {rel['label']}\n"  # Label might be translated

        list_lang_note = ""
        if language.lower() != "english":
            list_lang_note = f" (Names might be in {language.capitalize()})"

        return (
            abstraction_listing,
            context,
            len(abstractions),
            project_name,
            list_lang_note,
            learner_level,
            use_cache,
        )  # Return use_cache

    def exec(self, prep_res):
        (
            abstraction_listing,
            context,
            num_abstractions,
            project_name,
            list_lang_note,
            learner_level,
            use_cache,
        ) = prep_res  # Unpack use_cache
        print("Determining chapter order using LLM...")
        learner_profile = get_learner_level_profile(learner_level)
        # No language variation needed here in prompt instructions, just ordering based on structure
        # The input names might be translated, hence the note.
        prompt = f"""
Given the following project abstractions and their relationships for the project ```` {project_name} ````:

Abstractions (Index # Name){list_lang_note}:
{abstraction_listing}

Context about relationships and project summary:
{context}

If you are going to make a tutorial for ```` {project_name} ```` for a {learner_profile["label"]} learner, what is the best order to explain these abstractions, from first to last?
Use this learner level guidance while ordering:
{learner_profile["chapter"]}

Ideally, first explain the concepts that give this learner the strongest orientation. Then move to more detailed implementation or supporting concepts.

Output the ordered list of abstraction indices, including the name in a comment for clarity. Use the format `idx # AbstractionName`.

```yaml
- 2 # FoundationalConcept
- 0 # CoreClassA
- 1 # CoreClassB (uses CoreClassA)
- ...
```

Now, provide the YAML output:
"""
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0)) # Use cache only if enabled and not retrying

        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        ordered_indices_raw = yaml.safe_load(yaml_str)

        if not isinstance(ordered_indices_raw, list):
            raise ValueError("LLM output is not a list")

        ordered_indices = []
        seen_indices = set()
        for entry in ordered_indices_raw:
            try:
                if isinstance(entry, int):
                    idx = entry
                elif isinstance(entry, str) and "#" in entry:
                    idx = int(entry.split("#")[0].strip())
                else:
                    idx = int(str(entry).strip())

                if not (0 <= idx < num_abstractions):
                    raise ValueError(
                        f"Invalid index {idx} in ordered list. Max index is {num_abstractions-1}."
                    )
                if idx in seen_indices:
                    raise ValueError(f"Duplicate index {idx} found in ordered list.")
                ordered_indices.append(idx)
                seen_indices.add(idx)

            except (ValueError, TypeError):
                raise ValueError(
                    f"Could not parse index from ordered list entry: {entry}"
                )

        # Check if all abstractions are included
        if len(ordered_indices) != num_abstractions:
            raise ValueError(
                f"Ordered list length ({len(ordered_indices)}) does not match number of abstractions ({num_abstractions}). Missing indices: {set(range(num_abstractions)) - seen_indices}"
            )

        print(f"Determined chapter order (indices): {ordered_indices}")
        return ordered_indices  # Return the list of indices

    def post(self, shared, prep_res, exec_res):
        # exec_res is already the list of ordered indices
        shared["chapter_order"] = exec_res  # List of indices


class GenerateCodeReadingRoute(Node):
    def prep(self, shared):
        abstractions = shared["abstractions"]
        relationships = shared["relationships"]
        chapter_order = shared["chapter_order"]
        files_data = shared["files"]
        project_name = shared["project_name"]
        language = shared.get("language", "english")
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        use_cache = shared.get("use_cache", True)

        chapter_lines = []
        ordered_file_indices = []
        seen_file_indices = set()
        for i, abstraction_index in enumerate(chapter_order):
            if not (0 <= abstraction_index < len(abstractions)):
                continue

            chapter_num = i + 1
            abstraction = abstractions[abstraction_index]
            chapter_name = abstraction["name"]
            filename = make_chapter_filename(chapter_num, chapter_name)
            related_files = abstraction.get("files", [])
            file_refs = []
            for file_idx in related_files:
                if 0 <= file_idx < len(files_data):
                    path, _ = files_data[file_idx]
                    file_refs.append(f"{file_idx} # {path}")
                    if file_idx not in seen_file_indices:
                        ordered_file_indices.append(file_idx)
                        seen_file_indices.add(file_idx)

            chapter_lines.append(
                "\n".join(
                    [
                        f"- Chapter {chapter_num}: [{chapter_name}]({filename})",
                        f"  Abstraction index: {abstraction_index}",
                        f"  Description: {abstraction['description']}",
                        "  Relevant files:",
                        *[f"    - {file_ref}" for file_ref in file_refs],
                    ]
                )
            )

        file_listing = "\n".join(
            f"- {idx} # {files_data[idx][0]}" for idx in ordered_file_indices
        )

        relationship_lines = []
        for rel in relationships.get("details", []):
            from_idx = rel["from"]
            to_idx = rel["to"]
            from_name = abstractions[from_idx]["name"]
            to_name = abstractions[to_idx]["name"]
            relationship_lines.append(
                f"- {from_idx} ({from_name}) -> {to_idx} ({to_name}): {rel['label']}"
            )

        return {
            "project_name": project_name,
            "language": language,
            "learner_level": learner_level,
            "use_cache": use_cache,
            "project_summary": relationships.get("summary", ""),
            "chapter_context": "\n\n".join(chapter_lines),
            "file_listing": file_listing,
            "relationships_context": "\n".join(relationship_lines),
        }

    def exec(self, prep_res):
        project_name = prep_res["project_name"]
        language = prep_res["language"]
        learner_profile = get_learner_level_profile(prep_res["learner_level"])
        use_cache = prep_res["use_cache"]

        language_instruction = ""
        if language.lower() != "english":
            lang_cap = language.capitalize()
            language_instruction = f"IMPORTANT: Write the entire code reading route in **{lang_cap}**. Translate headings, checklist labels, explanations, and advice into {lang_cap}. Keep code identifiers, file paths, and Markdown links unchanged.\n\n"

        prompt = f"""
{language_instruction}Create a practical code reading route for the project `{project_name}`.

This route is for a learner whose main pain point is: "I cannot understand this project or where to start reading the code."

Learner level guidance:
{learner_profile["chapter"]}

Project summary:
{prep_res["project_summary"]}

Tutorial chapters and related files:
{prep_res["chapter_context"]}

Relationships between abstractions:
{prep_res["relationships_context"]}

Allowed source files. Only reference paths from this list:
{prep_res["file_listing"]}

Write a standalone Markdown document with:
- A clear `# Code Reading Route: {project_name}` heading, translated if needed.
- A short "how to use this route" introduction.
- 3 to 7 ordered stages. Each stage must include:
  - the goal of this stage,
  - the exact source files to read in order,
  - what to look for in those files,
  - the tutorial chapter links that help with this stage,
  - a "stop when you can answer..." checkpoint.
- A final short section for what to do when the reader gets stuck.

Important constraints:
- Do not invent files. Use only the allowed source files above.
- Do not paste large code blocks. This is a reading route, not another chapter.
- Make it concrete enough that the reader can open files and follow the path immediately.
- Match the depth and tone to the {learner_profile["label"]} learner level.
- Output only Markdown. Do not wrap it in Markdown code fences.
"""
        route_content = call_llm(
            prompt, use_cache=(use_cache and self.cur_retry == 0)
        )

        expected_heading = f"# Code Reading Route: {project_name}"
        if not route_content.strip().startswith("#"):
            route_content = f"{expected_heading}\n\n{route_content.strip()}"

        print("Generated code reading route.")
        return route_content

    def post(self, shared, prep_res, exec_res):
        shared["code_reading_route"] = exec_res


class GenerateInterviewQA(Node):
    def prep(self, shared):
        abstractions = shared["abstractions"]
        relationships = shared["relationships"]
        chapter_order = shared["chapter_order"]
        files_data = shared["files"]
        project_name = shared["project_name"]
        language = shared.get("language", "english")
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        interview_focus = normalize_interview_focus(shared.get("interview_focus", "general"))
        mastery_horizon = normalize_mastery_horizon(shared.get("mastery_horizon", "7d"))
        use_cache = shared.get("use_cache", True)

        chapter_context_lines = []
        for i, abstraction_index in enumerate(chapter_order):
            if not (0 <= abstraction_index < len(abstractions)):
                continue
            chapter_num = i + 1
            abstraction = abstractions[abstraction_index]
            chapter_name = abstraction["name"]
            chapter_filename = make_chapter_filename(chapter_num, chapter_name)

            related_files = []
            for file_idx in abstraction.get("files", []):
                if 0 <= file_idx < len(files_data):
                    related_files.append(f"{file_idx} # {files_data[file_idx][0]}")

            chapter_context_lines.append(
                "\n".join(
                    [
                        f"- Chapter {chapter_num}: [{chapter_name}]({chapter_filename})",
                        f"  Abstraction index: {abstraction_index}",
                        f"  Description: {abstraction['description']}",
                        "  Key files:",
                        *[f"    - {file_ref}" for file_ref in related_files],
                    ]
                )
            )

        relationship_lines = []
        for rel in relationships.get("details", []):
            from_idx = rel["from"]
            to_idx = rel["to"]
            from_name = abstractions[from_idx]["name"]
            to_name = abstractions[to_idx]["name"]
            relationship_lines.append(
                f"- {from_idx} ({from_name}) -> {to_idx} ({to_name}): {rel['label']}"
            )

        return {
            "project_name": project_name,
            "language": language,
            "learner_level": learner_level,
            "interview_focus": interview_focus,
            "mastery_horizon": mastery_horizon,
            "use_cache": use_cache,
            "project_summary": relationships.get("summary", ""),
            "chapter_context": "\n\n".join(chapter_context_lines),
            "relationships_context": "\n".join(relationship_lines),
        }

    def exec(self, prep_res):
        project_name = prep_res["project_name"]
        language = prep_res["language"]
        learner_profile = get_learner_level_profile(prep_res["learner_level"])
        focus_profile = get_interview_focus_profile(prep_res["interview_focus"])
        mastery_horizon = normalize_mastery_horizon(prep_res["mastery_horizon"])
        mastery_days = MASTERY_HORIZON_DAYS[mastery_horizon]
        use_cache = prep_res["use_cache"]

        language_instruction = ""
        if language.lower() != "english":
            lang_cap = language.capitalize()
            language_instruction = f"IMPORTANT: Write the entire interview Q&A document in **{lang_cap}**. Translate questions, answers, and interviewer follow-up prompts into {lang_cap}. Keep code identifiers, file paths, and Markdown links unchanged.\n\n"

        prompt = f"""
{language_instruction}Create a practical interview Q&A pack for this project: `{project_name}`.

Target scenario:
- Candidate is preparing for daily internship interviews focused on AI Agent engineering.
- Interview style is implementation-focused and asks for code-level understanding, architecture judgment, debugging ability, and practical tradeoffs.
- Interview focus direction: **{focus_profile["label"]}**.
- Focus guidance: {focus_profile["guidance"]}

Learner level guidance:
{learner_profile["chapter"]}

Project summary:
{prep_res["project_summary"]}

Core chapters and files:
{prep_res["chapter_context"]}

Relationships between abstractions:
{prep_res["relationships_context"]}

Output a standalone Markdown document with this exact structure:
1. `# Interview Q&A: {project_name}`
2. `## How To Use`
3. `## Quick Pitch`:
   Include a 60-second self-introduction script aligned to this project.
4. `## Core Questions`:
   Provide 12 interview questions.
   For each question include:
   - `Question`
   - `What interviewer is testing`
   - `Strong answer` (concise but concrete)
   - `Follow-up` (an interviewer may ask next)
   - `Code anchor` (specific file paths and/or chapter links to review)
5. `## Hands-on Drills`:
   Provide 5 short practical drills (e.g., trace a call path, debug a failure mode, refactor a boundary).
   For each drill include expected steps and what a good answer looks like.
6. `## Last-Minute Checklist`:
   10 bullet points for pre-interview review.

Constraints:
- Focus on this project's real architecture and code-reading output. Do not invent unrelated frameworks.
- Keep answers interview-ready: direct, technical, and practical.
- Match difficulty to the {learner_profile["label"]} level while staying useful for internship interviews.
- Bias question selection and drills toward the selected interview focus direction.
- Output only Markdown. Do not wrap it in Markdown code fences.
"""
        interview_qa = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))

        expected_heading = f"# Interview Q&A: {project_name}"
        if not interview_qa.strip().startswith("#"):
            interview_qa = f"{expected_heading}\n\n{interview_qa.strip()}"

        print("Generated interview Q&A pack.")
        return interview_qa

    def post(self, shared, prep_res, exec_res):
        shared["interview_qa"] = exec_res


class GenerateProjectMasteryReport(Node):
    def prep(self, shared):
        abstractions = shared["abstractions"]
        relationships = shared["relationships"]
        chapter_order = shared["chapter_order"]
        files_data = shared["files"]
        project_name = shared["project_name"]
        language = shared.get("language", "english")
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        interview_focus = normalize_interview_focus(shared.get("interview_focus", "general"))
        mastery_horizon = normalize_mastery_horizon(shared.get("mastery_horizon", "7d"))
        use_cache = shared.get("use_cache", True)

        chapter_context_lines = []
        for i, abstraction_index in enumerate(chapter_order):
            if not (0 <= abstraction_index < len(abstractions)):
                continue
            chapter_num = i + 1
            abstraction = abstractions[abstraction_index]
            chapter_name = abstraction["name"]
            chapter_filename = make_chapter_filename(chapter_num, chapter_name)
            related_files = []
            for file_idx in abstraction.get("files", []):
                if 0 <= file_idx < len(files_data):
                    related_files.append(f"{file_idx} # {files_data[file_idx][0]}")

            chapter_context_lines.append(
                "\n".join(
                    [
                        f"- Chapter {chapter_num}: [{chapter_name}]({chapter_filename})",
                        f"  Description: {abstraction['description']}",
                        "  Related files:",
                        *[f"    - {file_ref}" for file_ref in related_files],
                    ]
                )
            )

        relationship_lines = []
        for rel in relationships.get("details", []):
            from_idx = rel["from"]
            to_idx = rel["to"]
            from_name = abstractions[from_idx]["name"]
            to_name = abstractions[to_idx]["name"]
            relationship_lines.append(
                f"- {from_idx} ({from_name}) -> {to_idx} ({to_name}): {rel['label']}"
            )

        return {
            "project_name": project_name,
            "language": language,
            "learner_level": learner_level,
            "interview_focus": interview_focus,
            "mastery_horizon": mastery_horizon,
            "use_cache": use_cache,
            "project_summary": relationships.get("summary", ""),
            "chapter_context": "\n\n".join(chapter_context_lines),
            "relationships_context": "\n".join(relationship_lines),
        }

    def exec(self, prep_res):
        project_name = prep_res["project_name"]
        language = prep_res["language"]
        learner_profile = get_learner_level_profile(prep_res["learner_level"])
        focus_profile = get_interview_focus_profile(prep_res["interview_focus"])
        mastery_horizon = normalize_mastery_horizon(prep_res["mastery_horizon"])
        mastery_days = MASTERY_HORIZON_DAYS[mastery_horizon]
        use_cache = prep_res["use_cache"]

        language_instruction = ""
        if language.lower() != "english":
            lang_cap = language.capitalize()
            language_instruction = f"IMPORTANT: Write the entire project mastery report in **{lang_cap}**. Translate headings, explanations, and checklist items into {lang_cap}. Keep code identifiers, file paths, and Markdown links unchanged.\n\n"

        prompt = f"""
{language_instruction}Create a practical project mastery report for `{project_name}`.

Goal:
Turn this into a real learning assistant output, not a normal document dump.

Learner level guidance:
{learner_profile["chapter"]}

Interview focus direction:
- {focus_profile["label"]}
- {focus_profile["guidance"]}

Project summary:
{prep_res["project_summary"]}

Core chapters and files:
{prep_res["chapter_context"]}

Relationships between abstractions:
{prep_res["relationships_context"]}

Output a standalone Markdown document with this exact structure:
1. `# Project Mastery Report: {project_name}`
2. `## How To Use This Report`
3. `## Mastery Snapshot`:
   A concise current-state summary and top 3 learning priorities.
4. `## Project Entry`:
   Explain entrypoints, first files to open, and how to verify understanding.
5. `## Core Data Flow`:
   Explain end-to-end data/control flow with concrete file anchors and a minimal step list.
6. `## Key Module Responsibilities`:
   A table-like bullet list: module/file -> responsibility -> common confusion.
7. `## Extensibility Points`:
   Where to add features safely, what contracts to preserve, and pitfalls.
8. `## Interview High-Frequency Questions`:
   10 high-frequency questions with concise strong answers and code anchors.
9. `## {mastery_days}-Day Action Plan`:
   Daily learning tasks and clear completion checks.
10. `## Mastery Checklist`:
    Checklist across these must-have dimensions:
    - Project entry
    - Core data flow
    - Key module responsibilities
    - Extensibility points
    - Interview high-frequency questions

Constraints:
- Keep it concrete with code anchors (file paths and chapter links).
- Do not invent files/modules.
- The action plan must have exactly {mastery_days} daily checkpoints.
- Make the checklist measurable ("I can explain...", "I can trace...", "I can modify...").
- Keep tone practical and execution-oriented.
- Output only Markdown. Do not wrap it in Markdown code fences.
"""
        mastery_report = call_llm(
            prompt, use_cache=(use_cache and self.cur_retry == 0)
        )

        expected_heading = f"# Project Mastery Report: {project_name}"
        if not mastery_report.strip().startswith("#"):
            mastery_report = f"{expected_heading}\n\n{mastery_report.strip()}"

        print("Generated project mastery report.")
        return mastery_report

    def post(self, shared, prep_res, exec_res):
        shared["project_mastery_report"] = exec_res


class WriteChapters(BatchNode):
    def prep(self, shared):
        chapter_order = shared["chapter_order"]  # List of indices
        abstractions = shared[
            "abstractions"
        ]  # List of {"name": str, "description": str, "files": [int]}
        files_data = shared["files"]  # List of (path, content) tuples
        project_name = shared["project_name"]
        language = shared.get("language", "english")
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True

        # Get already written chapters to provide context
        # We store them temporarily during the batch run, not in shared memory yet
        # The 'previous_chapters_summary' will be built progressively in the exec context
        self.chapters_written_so_far = (
            []
        )  # Use instance variable for temporary storage across exec calls

        # Create a complete list of all chapters
        all_chapters = []
        chapter_filenames = {}  # Store chapter filename mapping for linking
        for i, abstraction_index in enumerate(chapter_order):
            if 0 <= abstraction_index < len(abstractions):
                chapter_num = i + 1
                chapter_name = abstractions[abstraction_index][
                    "name"
                ]  # Potentially translated name
                # Create safe filename (from potentially translated name)
                filename = make_chapter_filename(i + 1, chapter_name)
                # Format with link (using potentially translated name)
                all_chapters.append(f"{chapter_num}. [{chapter_name}]({filename})")
                # Store mapping of chapter index to filename for linking
                chapter_filenames[abstraction_index] = {
                    "num": chapter_num,
                    "name": chapter_name,
                    "filename": filename,
                }

        # Create a formatted string with all chapters
        full_chapter_listing = "\n".join(all_chapters)

        items_to_process = []
        for i, abstraction_index in enumerate(chapter_order):
            if 0 <= abstraction_index < len(abstractions):
                abstraction_details = abstractions[
                    abstraction_index
                ]  # Contains potentially translated name/desc
                # Use 'files' (list of indices) directly
                related_file_indices = abstraction_details.get("files", [])
                # Get content using helper, passing indices
                related_files_content_map = get_content_for_indices(
                    files_data, related_file_indices
                )

                # Get previous chapter info for transitions (uses potentially translated name)
                prev_chapter = None
                if i > 0:
                    prev_idx = chapter_order[i - 1]
                    prev_chapter = chapter_filenames[prev_idx]

                # Get next chapter info for transitions (uses potentially translated name)
                next_chapter = None
                if i < len(chapter_order) - 1:
                    next_idx = chapter_order[i + 1]
                    next_chapter = chapter_filenames[next_idx]

                items_to_process.append(
                    {
                        "chapter_num": i + 1,
                        "abstraction_index": abstraction_index,
                        "abstraction_details": abstraction_details,  # Has potentially translated name/desc
                        "related_files_content_map": related_files_content_map,
                        "project_name": shared["project_name"],  # Add project name
                        "full_chapter_listing": full_chapter_listing,  # Add the full chapter listing (uses potentially translated names)
                        "chapter_filenames": chapter_filenames,  # Add chapter filenames mapping (uses potentially translated names)
                        "prev_chapter": prev_chapter,  # Add previous chapter info (uses potentially translated name)
                        "next_chapter": next_chapter,  # Add next chapter info (uses potentially translated name)
                        "language": language,  # Add language for multi-language support
                        "learner_level": learner_level,  # Add learner level for audience-aware content
                        "use_cache": use_cache, # Pass use_cache flag
                        # previous_chapters_summary will be added dynamically in exec
                    }
                )
            else:
                print(
                    f"Warning: Invalid abstraction index {abstraction_index} in chapter_order. Skipping."
                )

        print(f"Preparing to write {len(items_to_process)} chapters...")
        return items_to_process  # Iterable for BatchNode

    def exec(self, item):
        # This runs for each item prepared above
        abstraction_name = item["abstraction_details"][
            "name"
        ]  # Potentially translated name
        abstraction_description = item["abstraction_details"][
            "description"
        ]  # Potentially translated description
        chapter_num = item["chapter_num"]
        project_name = item.get("project_name")
        language = item.get("language", "english")
        learner_level = normalize_learner_level(item.get("learner_level", "beginner"))
        use_cache = item.get("use_cache", True) # Read use_cache from item
        learner_profile = get_learner_level_profile(learner_level)
        print(f"Writing chapter {chapter_num} for: {abstraction_name} using LLM ({learner_level})...")

        # Prepare file context string from the map
        file_context_str = "\n\n".join(
            f"--- File: {idx_path.split('# ')[1] if '# ' in idx_path else idx_path} ---\n{content}"
            for idx_path, content in item["related_files_content_map"].items()
        )

        # Get summary of chapters written *before* this one
        # Use the temporary instance variable
        previous_chapters_summary = "\n---\n".join(self.chapters_written_so_far)

        # Add language instruction and context notes only if not English
        language_instruction = ""
        concept_details_note = ""
        structure_note = ""
        prev_summary_note = ""
        instruction_lang_note = ""
        mermaid_lang_note = ""
        code_comment_note = ""
        link_lang_note = ""
        tone_note = ""
        if language.lower() != "english":
            lang_cap = language.capitalize()
            language_instruction = f"IMPORTANT: Write this ENTIRE tutorial chapter in **{lang_cap}**. Some input context (like concept name, description, chapter list, previous summary) might already be in {lang_cap}, but you MUST translate ALL other generated content including explanations, examples, technical terms, and potentially code comments into {lang_cap}. DO NOT use English anywhere except in code syntax, required proper nouns, or when specified. The entire output MUST be in {lang_cap}.\n\n"
            concept_details_note = f" (Note: Provided in {lang_cap})"
            structure_note = f" (Note: Chapter names might be in {lang_cap})"
            prev_summary_note = f" (Note: This summary might be in {lang_cap})"
            instruction_lang_note = f" (in {lang_cap})"
            mermaid_lang_note = f" (Use {lang_cap} for labels/text if appropriate)"
            code_comment_note = f" (Translate to {lang_cap} if possible, otherwise keep minimal English for clarity)"
            link_lang_note = (
                f" (Use the {lang_cap} chapter title from the structure above)"
            )
            tone_note = f" (appropriate for {lang_cap} readers)"

        prompt = f"""
{language_instruction}Write {learner_profile["chapter_goal"]} tutorial chapter (in Markdown format) for the project `{project_name}` about the concept: "{abstraction_name}". This is Chapter {chapter_num}.

Learner level guidance:
{learner_profile["chapter"]}

Concept Details{concept_details_note}:
- Name: {abstraction_name}
- Description:
{abstraction_description}

Complete Tutorial Structure{structure_note}:
{item["full_chapter_listing"]}

Context from previous chapters{prev_summary_note}:
{previous_chapters_summary if previous_chapters_summary else "This is the first chapter."}

Relevant Code Snippets (Code itself remains unchanged):
{file_context_str if file_context_str else "No specific code snippets provided for this abstraction."}

Instructions for the chapter (Generate content in {language.capitalize()} unless specified otherwise):
- Start with a clear heading (e.g., `# Chapter {chapter_num}: {abstraction_name}`). Use the provided concept name.

- If this is not the first chapter, begin with a brief transition from the previous chapter{instruction_lang_note}, referencing it with a proper Markdown link using its name{link_lang_note}.

- Begin with a high-level motivation explaining what problem this abstraction solves{instruction_lang_note}. Start with a central use case as a concrete example. The whole chapter should guide the reader to understand how to solve this use case at a {learner_profile["label"]} level.

- If the abstraction is complex, break it down into key concepts. Explain each concept one-by-one at the requested learner level{instruction_lang_note}.

- Explain how to use this abstraction to solve the use case{instruction_lang_note}. Give example inputs and outputs for code snippets (if the output isn't values, describe at a high level what will happen{instruction_lang_note}).

- Each code block should be BELOW 10 lines! If longer code blocks are needed, break them down into smaller pieces and walk through them one-by-one. Simplify examples without hiding details that matter to a {learner_profile["label"]} learner. Use comments{code_comment_note} to skip non-important implementation details. Each code block should have a level-appropriate explanation right after it{instruction_lang_note}.

- Describe the internal implementation to help understand what's under the hood{instruction_lang_note}. First provide a non-code or code-light walkthrough on what happens step-by-step when the abstraction is called{instruction_lang_note}. It's recommended to use a simple sequenceDiagram with a dummy example - keep it minimal with at most 5 participants to ensure clarity. If participant name has space, use: `participant QP as Query Processing`. {mermaid_lang_note}.

- Then dive deeper into code for the internal implementation with references to files. Provide example code blocks and explanations that match the requested learner level{instruction_lang_note}.

- IMPORTANT: When you need to refer to other core abstractions covered in other chapters, ALWAYS use proper Markdown links like this: [Chapter Title](filename.md). Use the Complete Tutorial Structure above to find the correct filename and the chapter title{link_lang_note}. Translate the surrounding text.

- Use mermaid diagrams to illustrate complex concepts (```mermaid``` format). {mermaid_lang_note}.

- Use analogies and examples according to the learner level guidance above{instruction_lang_note}.

- End the chapter with a brief conclusion that summarizes what was learned{instruction_lang_note} and provides a transition to the next chapter{instruction_lang_note}. If there is a next chapter, use a proper Markdown link: [Next Chapter Title](next_chapter_filename){link_lang_note}.

- Ensure the tone is {learner_profile["closing_tone"]}{tone_note}.

- Output *only* the Markdown content for this chapter.

Now, directly provide the Markdown output for this learner level (DON'T need ```markdown``` tags):
"""
        chapter_content = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0)) # Use cache only if enabled and not retrying
        # Basic validation/cleanup
        actual_heading = f"# Chapter {chapter_num}: {abstraction_name}"  # Use potentially translated name
        if not chapter_content.strip().startswith(f"# Chapter {chapter_num}"):
            # Add heading if missing or incorrect, trying to preserve content
            lines = chapter_content.strip().split("\n")
            if lines and lines[0].strip().startswith(
                "#"
            ):  # If there's some heading, replace it
                lines[0] = actual_heading
                chapter_content = "\n".join(lines)
            else:  # Otherwise, prepend it
                chapter_content = f"{actual_heading}\n\n{chapter_content}"

        # Add the generated content to our temporary list for the next iteration's context
        self.chapters_written_so_far.append(chapter_content)

        return chapter_content  # Return the Markdown string (potentially translated)

    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list contains the generated Markdown for each chapter, in order
        shared["chapters"] = exec_res_list
        # Clean up the temporary instance variable
        del self.chapters_written_so_far
        print(f"Finished writing {len(exec_res_list)} chapters.")


class CombineTutorial(Node):
    def prep(self, shared):
        project_name = shared["project_name"]
        output_base_dir = shared.get("output_dir", "output")  # Default output dir
        output_path = os.path.join(output_base_dir, project_name)
        repo_url = shared.get("repo_url")  # Get the repository URL
        learner_level = normalize_learner_level(shared.get("learner_level", "beginner"))
        language = shared.get("language", "chinese")

        # Get potentially translated data
        relationships_data = shared[
            "relationships"
        ]  # {"summary": str, "details": [{"from": int, "to": int, "label": str}]} -> summary/label potentially translated
        chapter_order = shared["chapter_order"]  # indices
        abstractions = shared[
            "abstractions"
        ]  # list of dicts -> name/description potentially translated
        chapters_content = shared[
            "chapters"
        ]  # list of strings -> content potentially translated
        code_reading_route = shared.get("code_reading_route", "")
        interview_qa = shared.get("interview_qa", "")
        project_mastery_report = shared.get("project_mastery_report", "")

        # --- Generate Mermaid Diagram ---
        mermaid_lines = ["flowchart TD"]
        # Add nodes for each abstraction using potentially translated names
        for i, abstr in enumerate(abstractions):
            node_id = f"A{i}"
            # Use potentially translated name, sanitize for Mermaid ID and label
            sanitized_name = abstr["name"].replace('"', "")
            node_label = sanitized_name  # Using sanitized name only
            mermaid_lines.append(
                f'    {node_id}["{node_label}"]'
            )  # Node label uses potentially translated name
        # Add edges for relationships using potentially translated labels
        for rel in relationships_data["details"]:
            from_node_id = f"A{rel['from']}"
            to_node_id = f"A{rel['to']}"
            # Use potentially translated label, sanitize
            edge_label = (
                rel["label"].replace('"', "").replace("\n", " ")
            )  # Basic sanitization
            max_label_len = 30
            if len(edge_label) > max_label_len:
                edge_label = edge_label[: max_label_len - 3] + "..."
            mermaid_lines.append(
                f'    {from_node_id} -- "{edge_label}" --> {to_node_id}'
            )  # Edge label uses potentially translated label

        mermaid_diagram = "\n".join(mermaid_lines)
        # --- End Mermaid ---

        is_chinese = str(language).strip().lower() == "chinese"
        source_repo_title = "来源仓库" if is_chinese else "Source Repository"
        learner_level_title = "学习者水平" if is_chinese else "Learner Level"
        code_reading_section_title = "代码阅读路线" if is_chinese else "Code Reading Route"
        code_reading_desc = (
            "如果你还不确定应该从哪里开始读源码，请先看这里：[代码阅读路线](code_reading_route.md)。"
            if is_chinese
            else "Start here if you are not sure how to read the source code: [Code Reading Route](code_reading_route.md)."
        )
        interview_section_title = "面试准备" if is_chinese else "Interview Prep"
        interview_desc = (
            "面向 AI Agent 实习岗位的项目问答：[面试问答](interview_qa.md)。"
            if is_chinese
            else "Interview-focused Q&A for AI Agent internship prep: [Interview Q&A](interview_qa.md)."
        )
        learning_assistant_title = "学习助手" if is_chinese else "Learning Assistant"
        learning_assistant_desc = (
            "结构化学习进度与掌握检查点：[项目掌握度报告](project_mastery_report.md)。"
            if is_chinese
            else "Structured learning progress and mastery checkpoints: [Project Mastery Report](project_mastery_report.md)."
        )
        chapters_title = "章节目录" if is_chinese else "Chapters"
        index_title = f"# 教程：{project_name}\n\n" if is_chinese else f"# Tutorial: {project_name}\n\n"

        # --- Prepare index.md content ---
        index_content = index_title
        index_content += f"{relationships_data['summary']}\n\n"  # Use the potentially translated summary directly
        index_content += f"**{source_repo_title}:** [{repo_url}]({repo_url})\n\n"
        index_content += f"**{learner_level_title}:** {learner_level}\n\n"

        # Add Mermaid diagram for relationships (diagram itself uses potentially translated names/labels)
        index_content += "```mermaid\n"
        index_content += mermaid_diagram + "\n"
        index_content += "```\n\n"

        chapter_files = []
        if code_reading_route:
            index_content += f"## {code_reading_section_title}\n\n"
            index_content += f"{code_reading_desc}\n\n"

            route_content = code_reading_route
            if not route_content.endswith("\n\n"):
                route_content += "\n\n"
            route_content += "---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"
            chapter_files.append(
                {"filename": "code_reading_route.md", "content": route_content}
            )

        if interview_qa:
            index_content += f"## {interview_section_title}\n\n"
            index_content += f"{interview_desc}\n\n"

            interview_qa_content = interview_qa
            if not interview_qa_content.endswith("\n\n"):
                interview_qa_content += "\n\n"
            interview_qa_content += "---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"
            chapter_files.append(
                {"filename": "interview_qa.md", "content": interview_qa_content}
            )

        if project_mastery_report:
            index_content += f"## {learning_assistant_title}\n\n"
            index_content += f"{learning_assistant_desc}\n\n"

            mastery_report_content = project_mastery_report
            if not mastery_report_content.endswith("\n\n"):
                mastery_report_content += "\n\n"
            mastery_report_content += "---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"
            chapter_files.append(
                {
                    "filename": "project_mastery_report.md",
                    "content": mastery_report_content,
                }
            )

        index_content += f"## {chapters_title}\n\n"

        # Generate chapter links based on the determined order, using potentially translated names
        for i, abstraction_index in enumerate(chapter_order):
            # Ensure index is valid and we have content for it
            if 0 <= abstraction_index < len(abstractions) and i < len(chapters_content):
                abstraction_name = abstractions[abstraction_index][
                    "name"
                ]  # Potentially translated name
                # Sanitize potentially translated name for filename
                filename = make_chapter_filename(i + 1, abstraction_name)
                index_content += f"{i+1}. [{abstraction_name}]({filename})\n"  # Use potentially translated name in link text

                # Add attribution to chapter content (using English fixed string)
                chapter_content = chapters_content[i]  # Potentially translated content
                if not chapter_content.endswith("\n\n"):
                    chapter_content += "\n\n"
                # Keep fixed strings in English
                chapter_content += f"---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"

                # Store filename and corresponding content
                chapter_files.append({"filename": filename, "content": chapter_content})
            else:
                print(
                    f"Warning: Mismatch between chapter order, abstractions, or content at index {i} (abstraction index {abstraction_index}). Skipping file generation for this entry."
                )

        # Add attribution to index content (using English fixed string)
        index_content += f"\n\n---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"

        return {
            "output_path": output_path,
            "index_content": index_content,
            "chapter_files": chapter_files,  # List of {"filename": str, "content": str}
        }

    def exec(self, prep_res):
        output_path = prep_res["output_path"]
        index_content = prep_res["index_content"]
        chapter_files = prep_res["chapter_files"]

        print(f"Combining tutorial into directory: {output_path}")
        # Rely on Node's built-in retry/fallback
        os.makedirs(output_path, exist_ok=True)

        # Write index.md
        index_filepath = os.path.join(output_path, "index.md")
        with open(index_filepath, "w", encoding="utf-8") as f:
            f.write(index_content)
        print(f"  - Wrote {index_filepath}")

        # Write chapter files
        for chapter_info in chapter_files:
            chapter_filepath = os.path.join(output_path, chapter_info["filename"])
            with open(chapter_filepath, "w", encoding="utf-8") as f:
                f.write(chapter_info["content"])
            print(f"  - Wrote {chapter_filepath}")

        return output_path  # Return the final output path

    def post(self, shared, prep_res, exec_res):
        shared["final_output_dir"] = exec_res  # Store the output path
        print(f"\nTutorial generation complete! Files are in: {exec_res}")
