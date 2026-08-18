# Diary: evidence-grounded originality revision

This task adds a local, traceable originality-remediation layer between ARS
integrity checking and Word/WPS publication formatting.

## Step 1: Define and implement the bounded skill

### Prompt Context

**Verbatim prompt:**

> PLEASE IMPLEMENT THIS PLAN:
> # 为科研 Workflow 增加“可追溯论文原创性修订”功能
>
> ## 总结
>
> 在现有流程中加入一个独立的原创性修订层：
>
> `Zotero 证据 → Obsidian 语义稿 → ARS 完整性检查 → 原创性修订 → 重新验证 → 投稿格式化 → Word/WPS`
>
> 现有 `academic-research-suite` 已经提供 `ORIGINAL / PARAPHRASE / CLOSE_MATCH / VERBATIM` 检测。因此按照最小技能原则，新增 `revise-originality-with-evidence`，只补齐“发现问题后的证据化修订”，不重复开发查重系统，也不侵入 Word/WPS 排版层。
>
> ## 核心实现
>
> - 将原创性修订作为 Stage 2.5 和 Stage 4.5 完整性检查中的修复回路：Phase D 检出 `MODERATE` 及以上问题；新技能读取问题段落、Zotero 来源和查重报告；生成独立修订稿和变更账本；对全部修改段落重新执行 Phase D、引用、数据和事实验证；只有零未解决 `CRITICAL / SERIOUS / MODERATE` 问题的稿件才能进入 `format-submission-manuscript`。
> - 新增统一接口：`doctor`、`import-report`、`analyze`、`revise`、`verify`。
> - 使用 `originality.yaml` 描述原始稿、ARS 报告、Better BibTeX 数据、Zotero 证据、查重报告、语言、受保护内容、输出和复核要求。
> - 把不同查重系统统一为标准化匹配记录；不支持的报告版本必须明确失败并提供通用 CSV/JSON 模板。
>
> ## 修订与安全规则
>
> - 每个待修改段落必须重新读取对应 Zotero 文献及页码，先产生“来源含义摘要”，再从摘要重写，禁止围绕匹配文本机械换词。
> - 锁定数字、样本量、效应值、单位、量表名称、干预名称、统计方法、表图编号、citation key 和结论方向。
> - 缺少原始来源、来源无法支持论断或语义存在歧义时停止自动改写并标为阻断问题。
> - 直接引语应规范引用；方法学标准术语、报告规范和通用表达不强制改写；自我重复按政策与语境判断。
> - 相似度只作为定位信号，不把目标设定为某个百分比。
> - 所有报告默认仅在本地处理，不自动登录、抓取或绕过知网、Turnitin、iThenticate 的授权体系。
> - 报告和论文均作为不可信输入处理。
> - 生成 `manuscript-originality-reviewed.md`、`normalized-matches.json`、`change-ledger.md/json`、`originality-qa-report.md/json`、`ai-use-disclosure-draft.md` 和 SHA-256 清单。
> - 原稿永不覆盖；修订副本通过完整性复核并获得最终确认后才进入格式化。
>
> ## 仓库、测试与验收
>
> - 在仓库增加轻量 Codex 技能、Windows/macOS 幂等安装入口，并更新组件锁、架构图、中英文 README 和故障排查文档。
> - 保持 `format-submission-manuscript` 只负责版式；原创性技能只能输出语义 Markdown，不直接操作 DOCX、Word 或 WPS。
> - 提供脱敏测试夹具，覆盖知网、Turnitin、iThenticate、通用格式、中英文和跨语言、自我重复、数字保护、标准术语、格式变化、缺失来源、恶意指令和幂等性。
> - 端到端验收必须证明原稿未覆盖、每个修改可追溯、科学不变量保持、100% 修改段落复核、未解决问题阻止 Word/WPS、重复运行等价，并且不宣称官方分数或保证某个比例。
>
> 默认采用中英双语、用户导出报告导入、独立修订副本加最终复核；第一版不接商业查重账户或 API。

**Interpretation:** Build the approved implementation in the existing public
workflow repository, install it locally, and prove the safety and handoff gates
with executable tests.

**Inferred intent:** Add a useful originality-repair capability without
duplicating the upstream detector, weakening source provenance, or turning the
workflow into plagiarism-detection evasion.

### What I did

I read `/AGENTS.md`, the skill-creation contract, the ARS router and pipeline
integrity contract, then initialized `/codex/skills/revise-originality-with-evidence`.
The skill defines a local five-command interface (`doctor`, `import-report`,
`analyze`, `revise`, and `verify`), strict project and report schemas, a private
project starter, a deterministic Python helper, cross-platform wrappers, and a
hash-bound gate consumed by `/codex/skills/format-submission-manuscript`.

I ran `/scripts/Install-OriginalityRevision.ps1`. It created the isolated
runtime, installed PyYAML 6.0.3 and pypdf 6.16.1, copied the skill to the local
Codex skills directory, and passed `doctor --self-test` on Python 3.12.13.

### Why

ARS already detects `CLOSE_MATCH`, `VERBATIM`, and self-reuse. A narrow
remediation adapter preserves the existing ownership boundary: Zotero supplies
evidence, Obsidian supplies semantic Markdown, ARS supplies integrity review,
the new skill creates a reviewable repair copy, and Word/WPS remains layout-only.

### What worked

The installer was idempotent in shape and the first live doctor run reported all
declared dependencies and report adapters available. The helper compiled after
one local f-string correction, and its internal self-test mapped a synthetic
Turnitin finding to a stable manuscript paragraph.

### What didn't work

The first unit-test command was:

`python -m unittest discover -s codex\skills\revise-originality-with-evidence\tests -v`

It failed while dynamically importing the helper with:

`AttributeError: 'NoneType' object has no attribute '__dict__'`

The traceback originated in `dataclasses._is_type` because the test loader had
not inserted the dynamically created `originality_revision` module into
`sys.modules` before `exec_module`. The fixture now registers the module first.

After the 11 originality tests passed, the first skill-validation command also
failed on this Chinese-locale Windows host:

`python quick_validate.py codex\skills\revise-originality-with-evidence`

The exact error was
`UnicodeDecodeError: 'gbk' codec can't decode byte 0xae in position 4422`.
The bundled validator calls `Path.read_text()` without an encoding, so the
repository's valid UTF-8 Chinese guidance was decoded as the system code page.
Validation is rerun with `PYTHONUTF8=1`; the source text is intentionally not
degraded to work around a validator-locale assumption.

A later attempt to delete ignored `__pycache__` files through the shell was
rejected by the execution safety policy before it ran. Those generated files
remain ignored and untracked; no repository source was changed by the rejected
cleanup command.

### What I learned

The Python 3.12 dataclass implementation expects a dynamically imported module
to be discoverable through `sys.modules`. The production CLI import path was
not affected; this was isolated to the unit-test loader.

Skill validation on Windows must force UTF-8 when the active ANSI code page is
not UTF-8.

### What was tricky

Semantic rewriting cannot safely be delegated to a deterministic CLI. The
implementation therefore makes Codex/Zotero produce evidence-backed proposals
and reserves the script for report normalization, exact paragraph application,
invariant checks, recheck coverage, approval state, and provenance hashes.

### What warrants review

Review `/codex/skills/revise-originality-with-evidence/SKILL.md`, the strict
proposal/evidence checks in `/codex/skills/revise-originality-with-evidence/scripts/originality_revision.py`,
and the `originality_manifest` hard gate added to the publication formatter.

### Future work

Vendor layouts evolve. Add a parser only from a sanitized, authorized fixture;
unsupported layouts should continue to fail closed and fall back to generic
CSV/JSON.

## Step 2: Integrate, install, and validate the release path

### Prompt Context

**Verbatim prompt:** “PLEASE IMPLEMENT THIS PLAN” for the approved
evidence-grounded originality-revision layer, including repository integration,
cross-platform installation, formatter gating, and end-to-end acceptance.

**Interpretation:** Complete the feature as a working part of the local and
public workflow rather than stopping at an isolated skill scaffold.

**Inferred intent:** A manuscript with unresolved originality findings must be
unable to reach Word/WPS, while an evidence-checked and explicitly approved copy
must still pass through the established publication backend.

### What I did

I added `/docs/originality-revision.md`, updated both READMEs, architecture,
component lock, security model, plugin matrix, publication documentation,
Codex contract, citation metadata, GitHub Actions, and the repository validator.
I added Windows/macOS installers and wrappers plus
`/prompts/06-setup-originality-revision.md`.

The publication formatter now accepts `originality_manifest`. Before Pandoc or
Word/WPS starts, it requires `qa_passed`, the exact configured manuscript
SHA-256, and explicit named approval. The formatter records that manifest in its
run provenance while remaining layout-only.

I ran the originality installer twice to prove idempotent dependency detection,
then resynchronized the publication skill with `-SkipApplications`. The final
formatter doctor detected Pandoc 3.10, LibreOffice, Poppler, and WPS; genuine
Microsoft Word correctly remained `not_checked` because its COM registration is
served by WPS.

### Why

A documented skill without an enforced downstream gate would still allow an
unreviewed copy to be formatted. Binding the QA status to the manuscript hash
turns the ethical and evidence rules into an executable release contract.

### What worked

The originality suite passed 11 tests. The publication suite passed 9 tests,
including real local WPS automation from an approved synthetic originality copy
through reviewed DOCX, PDF export, reopen/structure handling, and rasterization.
The skill validator passed under UTF-8, the public repository validator passed,
all JSON/YAML parsed, local Markdown links resolved, and `git diff --check`
reported no whitespace errors.

### What didn't work

The Windows `bash` command resolves to a WSL relay on this host, but the WSL
image has no `/bin/bash`; both attempted `bash -n` calls returned
`execvpe(/bin/bash) failed: No such file or directory`. The macOS scripts are
therefore locally `not_checked`. GitHub Actions now runs `bash -n` on all four
macOS helpers under Ubuntu, so the remote validation is explicit rather than
being inferred from the failed local relay.

### What I learned

The existing publication bridge can enforce a semantic integrity handoff
without acquiring ownership of the content. A small status/hash/approval
contract was sufficient; no rewrite logic had to enter the formatter.

### What was tricky

The report adapters must be useful without overstating support for changing
vendor layouts. Deterministic JSON/CSV is the reliable interchange format;
PDF/HTML extraction remains fail-closed, and cross-language matches are routed
to semantic review instead of being assigned a false lexical confidence.

### What warrants review

Review the vendor-field normalizer, the paragraph mapping threshold, the
proposal invariant checks, and the new WPS acceptance test. On macOS, run both
new `.command` files and the doctor in a real Codex environment before claiming
a macOS runtime pass.

### Future work

When a sanitized real export demonstrates a new vendor layout, add one focused
adapter fixture and regression test. Commercial API or account automation stays
out of scope unless a future user supplies authorization and explicitly requests
that integration.
