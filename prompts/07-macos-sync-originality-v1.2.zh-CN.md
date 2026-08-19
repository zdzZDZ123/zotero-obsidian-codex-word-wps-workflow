# Mac Codex 增量部署原创性修订层 1.2.0

你现在直接操作这台 Mac，完成已有 Zotero–Obsidian–Codex–Word/WPS 科研工作流的
原创性修订（论文降重）功能增量部署。不要只给我计划或命令说明；请实际检查、安装、
配置、运行测试并给出证据。除非遇到必须由我输入的管理员密码、商业软件登录或授权，
否则无需逐项询问我。

## 已知前提与目标

- 这台 Mac 已经完成 Zotero、Obsidian、Codex、Microsoft Word 和 WPS 的原有打通。
- 本次只新增或升级 `revise-originality-with-evidence`，不得重装、重置或改变上述软件
  以及 `format-submission-manuscript`、`academic-research-suite` 的现有配置。
- 公开源仓库：
  `https://github.com/zdzZDZ123/zotero-obsidian-codex-word-wps-workflow.git`
- 必须包含最低基线提交：
  `e599ec9a4c3639a99069f7824ac62b250feab5e0`
- 目标技能版本必须为 `1.2.0` 或更高兼容版本。
- 目标流程：
  `Zotero 证据 → Obsidian 语义稿 → ARS Phase D → 证据化原创性修订 →
  查重报告门禁 → DOCX/PDF → Word/WPS`。

“不高于 10%”只能作为读取用户合法导出的知网、Turnitin 或 iThenticate 全文报告后的
投稿放行门槛，不能承诺任何论文必然达到该分数，也不能使用同义词机械替换、翻译绕过、
零宽字符、同形字符、隐藏文字、图片化文字或其他规避检测的方法。

## 一、检查环境并保护已有配置

1. 确认 `uname -s` 为 `Darwin`，记录芯片架构、macOS 版本、当前 shell、`CODEX_HOME`
   （默认 `$HOME/.codex`）、Python 3 和 Git 状态。
2. 只读确认以下现有组件，不修改其设置：
   - `$CODEX_HOME/skills/academic-research-suite`
   - `$CODEX_HOME/skills/format-submission-manuscript`
   - `/Applications/Microsoft Word.app` 或实际 Word 路径
   - `/Applications/wpsoffice.app`、`/Applications/WPS Office.app` 或实际 WPS 路径
   - Obsidian vault 与 Zotero 数据目录只确认存在，不复制、不上传、不输出私人内容。
3. 对本次会修改的 `$CODEX_HOME/skills/revise-originality-with-evidence`，如果已经存在，
   先记录版本和文件 SHA-256。安装脚本本身是幂等的；不要删除整个 `$CODEX_HOME`，不要
   清理其他技能或运行时。

## 二、获得可信源代码

1. 优先在当前目录、`$HOME/Documents`、`$HOME/Downloads` 中寻找仓库目录
   `zotero-obsidian-codex-word-wps-workflow`。
2. 找到 Git 仓库时：
   - 先运行 `git status --short --branch`；
   - 如果工作树干净，使用 HTTPS 执行 `git fetch origin` 和 `git pull --ff-only`；
   - 如果有用户改动，不得 reset、checkout、stash 或覆盖，改为克隆一份临时干净副本。
3. 没找到时，使用 HTTPS 克隆到
   `$HOME/Documents/zotero-obsidian-codex-word-wps-workflow`。
4. 如果 Git 网络失败，可以从同一 GitHub 仓库下载 `main.zip`，用 macOS 自带 `ditto`
   解压到独立临时目录；不得从第三方镜像下载代码。
5. 验证仓库包含上述最低基线提交。Git 仓库执行：

   ```bash
   git merge-base --is-ancestor e599ec9a4c3639a99069f7824ac62b250feab5e0 HEAD
   ```

   ZIP 来源则检查以下文件和内容：
   - `codex/skills/revise-originality-with-evidence/SKILL.md` 的版本至少为 `1.2.0`；
   - `originality.yaml` 包含 `max_overall_similarity_percent: 10`、
     `max_report_age_days: 30` 和 `require_report_after_revision: true`；
   - 脚本含有 `attest-release` 命令。

## 三、实际安装到 Mac Codex

在可信仓库根目录执行：

```bash
chmod +x ./scripts/Install-OriginalityRevision-macOS.command
chmod +x ./scripts/Revise-ResearchOriginality-macOS.command
bash ./scripts/Install-OriginalityRevision-macOS.command
bash ./scripts/Revise-ResearchOriginality-macOS.command doctor --self-test --json
```

要求：

- 使用 `$CODEX_HOME/runtimes/originality-revision` 隔离 Python 环境。
- 依赖只能来自技能的 `requirements.txt`。
- 如果缺少 Python 3，可以在已有 Homebrew 时执行 `brew install python`；没有 Homebrew 时
  停止并准确说明，不要擅自安装 Homebrew。
- 安装后比较仓库与已安装技能中 `originality_revision.py` 的 SHA-256，必须一致。
- 再次读取已安装的 `SKILL.md`，确认版本至少为 `1.2.0`。

## 四、运行完整自动验证

使用隔离运行时运行原创性测试，不使用系统 Python：

```bash
"${CODEX_HOME:-$HOME/.codex}/runtimes/originality-revision/bin/python" \
  -m unittest discover \
  -s ./codex/skills/revise-originality-with-evidence/tests \
  -v
```

不得只看退出码。逐项确认测试输出至少覆盖：

1. 全文 21% 时为 `qa_failed`，不能进入 Word/WPS。
2. 全文 9.8% 且其他检查通过时才能产生 `qa_passed`。
3. 单条命中的 21% 不得被误判为全文 21%。
4. 同一平台的新报告替换旧报告，不累积旧分数。
5. 新报告写入后立即清除旧 `qa_passed`。
6. 报告平台标识与声明不一致时失败关闭。
7. 报告早于当前修订稿或超过 30 天时失败关闭。
8. 修订稿、查重报告或复核结果哈希变化时，旧批准失效。
9. 数字、样本量、单位、citation key、受保护术语、表图引用和结论方向保持不变。
10. 知网 `总文字复制比`、Turnitin 和 iThenticate 的明确全文标签能被识别；冲突标签
    必须失败关闭。

如果已经存在投稿格式化运行时，再运行平台无关的格式化器门禁测试或完整测试套件，确认
`format-submission-manuscript` 仍然只接受 `qa_passed`。不要为了测试改变 Word/WPS 的用户
模板或默认设置。若 macOS 上某项编辑器自动化测试不适用，必须明确标为 `not_checked`，
不能伪造通过。

## 五、建立私有项目模板，但不接触真实论文

1. 从仓库复制
   `codex/skills/revise-originality-with-evidence/assets/project-starter`
   到 `$HOME/Documents/ResearchWorkflow-Private/originality-project-starter-v1.2`。
2. 如果目标目录已存在，不覆盖，创建带时间戳的新目录。
3. 将目录权限设为仅当前用户可读写执行：`chmod -R go-rwx <目录>`。
4. 不把真实论文、Zotero 数据、PDF、查重报告或身份信息写入公开仓库。
5. 只使用仓库中的脱敏合成夹具完成冒烟测试。

## 六、确认实际论文使用命令

在最终报告中给出适合本机真实路径的命令示例，至少包括：

```bash
bash ./scripts/Revise-ResearchOriginality-macOS.command analyze --config /私有项目/originality.yaml
bash ./scripts/Revise-ResearchOriginality-macOS.command revise --config /私有项目/originality.yaml
bash ./scripts/Revise-ResearchOriginality-macOS.command attest-release \
  --config /私有项目/originality.yaml \
  --report /私有项目/reports/post-revision.pdf \
  --vendor turnitin \
  --reviewer "Author review" \
  --report-generated-at "带时区的 ISO-8601 时间"
bash ./scripts/Revise-ResearchOriginality-macOS.command verify --config /私有项目/originality.yaml
bash ./scripts/Revise-ResearchOriginality-macOS.command verify \
  --config /私有项目/originality.yaml --approve --reviewer "Author review"
```

必须说明：`attest-release` 读取用户导出的全文分数并绑定修订稿/报告哈希；它不会登录查重
平台。高于 10%、报告过期或证据/复核失败时，Word/WPS 投稿格式化必须保持阻断。

## 七、完成标准与最终回报

只有同时满足以下条件才能报告“部署完成”：

- 已安装技能版本至少为 `1.2.0`；
- `doctor --self-test` 通过；
- 原创性测试全部通过；
- 仓库脚本与安装脚本 SHA-256 一致；
- 10% 门禁、30 天时效、修订后报告要求、平台一致性和旧批准撤销均有测试证据；
- 已确认不会覆盖 Zotero、Obsidian、Word、WPS 或其他 Codex 技能配置；
- 已创建私有项目模板且没有使用真实论文数据；
- 明确提示重启 Codex 后再在 `/skills` 中确认
  `revise-originality-with-evidence`，不得声称当前会话已动态重新加载技能。

最后用中文给出：实际仓库路径、提交哈希、安装路径、技能版本、Python/依赖版本、测试数量
与结果、Word/WPS 门禁验证状态、私有模板路径、未检查项目和任何偏差。失败时保留现场，
给出精确错误与下一条安全命令，不要用“应该可以”代替验证。
