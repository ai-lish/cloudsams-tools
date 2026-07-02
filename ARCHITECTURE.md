# cloudsams-tools — Architecture

> Version: v1 · 2026-07-02
> Scope: monorepo layout、tool entrypoint contract、shared code 邊界、discoverability。
> 呢份 doc 講「點解咁揀」；`CONTRIBUTING.md` 講「點樣加 tool」嘅 step-by-step。

---

## 0. 三個 Goal（做決定嘅準繩）

| Goal | 意思 | 對架構嘅硬要求 |
|---|---|---|
| **G1 低成本加 tool** | 加一個 tool = 開一個 folder，最少 boilerplate | 加 tool **唔使改中央 registry** |
| **G2 loose coupling** | 改／擴展一個 tool 唔會撞到其他 tool | tool 之間**唔准 import 對方**；shared code 有守門 |
| **G3 discoverability** | `cloudsams list` 睇齊所有 tool，唔使 grep | 有一個**唔使 import tool 就讀到**嘅 metadata 來源 |

呢三個 goal 之間有張力，主要係 **G3（統一入口）vs G2（零耦合）**。以下每個決定都要交代點樣兩者兼得。

---

## 1. 核心決定：Unified CLI，但用 auto-discovery + lazy import 實現

### 1.1 打破「統一 CLI vs 獨立 script」嘅二分法

問題 Q1 表面上係二選一：

- **統一 CLI**（`cloudsams split-pdf ...`）：discoverability、UX 一致 —— 但傳統做法要一個**中央 registry**（每加一個 tool 就 import / 登記一次），直接踩 G1 同 G2。
- **獨立 script**（`python tools/slp-split-pdf/split.py ...`）：零耦合 —— 但冇 discoverability，UX 各自為政。

呢個二分法係**假**嘅。真正踩 G1/G2 嘅唔係「統一入口」本身，而係「**中央 registry**」同「**啟動時 import 晒所有 tool**」。只要 dispatcher 用 **runtime 掃 folder** 嚟搵 tool，而且**只 import 被叫嗰一個 tool**，就可以三個 goal 全中。

### 1.2 揀咗：Auto-discovering thin dispatcher（雙模式）

```
cloudsams list                       # 掃 tools/*/tool.yaml，唔 import 任何 tool
cloudsams slp-split-pdf --input x.pdf # 只 import tools/slp-split-pdf/main.py
```

同時，**每個 tool 保持可獨立行**（backward-compatible）：

```
cd tools/slp-split-pdf && python split.py --input x.pdf --output-dir ./output
```

### 1.3 三個關鍵性質（點解呢個設計唔踩 goal）

1. **無中央 registry（滿足 G1 + G2）**
   Dispatcher 唔 hardcode 任何 tool 名。「有邊啲 tool」= `tools/` 底下有邊啲 folder 有 `tool.yaml`。加 tool 只係開 folder，**唔 touch 任何共用檔案**。

2. **Lazy per-tool import（滿足 G2 —— 故障隔離）**
   `cloudsams list` **完全唔 import** tool（淨係讀 manifest 文字），所以就算某個 tool 未 `pip install` 依賴、甚至 `main.py` 有 syntax error，`list` 同**其他 tool 照行**。`cloudsams <name>` 只 import `<name>` 一個。
   ⇒ 「一個 tool 壞／缺 dep」**唔會拖冧成個 CLI**。呢點係統一入口能夠共存於 G2 嘅關鍵。

3. **Dispatcher core 零第三方依賴（滿足 G2 + 可靠 G3）**
   `cloudsams_tools/`（dispatcher + discovery + lib）**只用 Python stdlib**。連 manifest 都用內建 mini-parser 讀（唔拉 PyYAML）。因此 `cloudsams list` 喺一個乾淨 clone、乜 dep 都未裝嘅情況下都行到。

### 1.4 Two-level argument dispatch（點解唔用 `subparsers.add_parser`）

傳統 argparse subcommand 要**一次過 import 晒**所有 tool 嚟砌 subparser tree —— 違反 lazy import。所以用**兩層**：

- 頂層 parser 只識 `list`、`--help`，同埋「第一個位置參數 = tool 名」。
- 其餘 argv **原封不動**傳落選中 tool 自己嘅 argparse。

即係 `cloudsams slp-split-pdf --mode range --pages 1-5` →
dispatcher 認得 `slp-split-pdf` → import 佢 `main.py` → 叫 `main.run(["--mode","range","--pages","1-5"])`。
每個 tool **擁有自己完整嘅 argparse / `--help`**，UX 一致但實作獨立。

---

## 2. Entrypoint contract（Q2）：Convention-first + 一個細 manifest

揀咗 **convention + lightweight manifest** 嘅混合，唔用 plugin registry（太重、要 tool 主動 register，撞 G2）。

### 2.1 硬 contract（唯一必守兩條）

一個 folder 要成為 tool，只需要兩樣嘢：

1. **`tools/<name>/tool.yaml`** —— 純 metadata，畀 `list` 同 dispatcher 用，**唔使 import** 就讀到。
2. **`tools/<name>/main.py`** 入面有

   ```python
   def run(argv: list[str] | None = None) -> int: ...
   ```

   收 CLI 參數 list，做嘢，return exit code。冇喇。

> 為何 convention 定 entrypoint、manifest 定 metadata？
> — **執行**要 import 先做到，梗係用 code convention（`run()`）。
> — **列表**唔應該為咗知個 summary 就 import／執行 tool（慢、有 side-effect、會被缺 dep 連累），所以 metadata 抽做靜態 manifest。各司其職。

### 2.2 `tool.yaml`（flat、mini-YAML subset）

```yaml
# tools/slp-split-pdf/tool.yaml
name: slp-split-pdf              # 要同 folder 名一致
summary: Split CloudSAMS SLP PDF into per-page / per-range files
status: stable                  # stable | beta | wip
runtime: python                 # python | node
entry: main.py                  # 預設 main.py，可省
requires_python: ">=3.10"
```

只支援 flat `key: value`（討論見 §5.2）。要新增 field 就直接加，dispatcher 唔認得嘅 key 會忽略。

### 2.3 為何唔揀 plugin registry / Python entry-points

- entry-points 要 `pip install -e` 每個 tool + 一個 `pyproject.toml`／`setup.py` per tool → boilerplate 爆升，踩 G1。
- 「tool 主動 register 入 base class」= import-time side effect，要 import 先見到 → 撞 lazy import / 故障隔離。
- 我哋要嘅係「開 folder 就得」，convention + 靜態 manifest 剛好。

---

## 3. Shared base（Q3）：薄、opt-in、只提供樣板消除

`cloudsams_tools/lib/base.py` 存在嘅唯一理由：**消除每個 tool 都要重寫嘅樣板**。它係**可選**嘅 —— 唔用都照行（`run(argv)` 先係 contract）。

### 3.1 base 提供（白名單）

| Helper | 解決乜 |
|---|---|
| `add_common_io_args(parser)` | 統一 `--input` / `--output-dir` 嘅 flag 名、type=Path、help 文字 |
| `resolve_output_dir(path)` | `mkdir(parents=True, exist_ok=True)` + 統一 output 命名慣例 |
| `get_logger(tool_name)` | 統一 log 格式（stderr、`✂️`/`✅` 之類 emoji prefix 由 tool 自己決定） |
| `die(msg, code=1)` | 統一錯誤退出（印 `❌ ...` 落 stderr、return code） |
| `Tool` (dataclass, 可選) | 想結構化嘅 tool 可以繼承，攞到 `self.log` / `self.args`；純方便 |

### 3.2 base **唔**提供（明確排除）

- ❌ 任何 tool 業務邏輯（PDF、CSV、rename 全部係 tool 自己嘅事）。
- ❌ I/O 抽象層 / plugin framework / DI container —— over-engineering，撐大 coupling surface。
- ❌ 強制 base class：contract 係 `run(argv)`，唔係「必須繼承」。
- ❌ 共用第三方 dep：base 只用 stdlib，唔可以令 `list` 要裝 pypdf。

> 準則：**一樣嘢要入 base，先要「≥2 個 tool 真係用緊」+「stable」+「domain-neutral」**。淨係「睇落可以共用」唔算數 —— 見 §4.2。

---

## 4. 「改一個 tool 唔影響其他」點體現（Q4）

### 4.1 目錄樹（最終版）

```
cloudsams-tools/
├── ARCHITECTURE.md              # 呢份
├── README.md · SECURITY.md · CONTRIBUTING.md · .gitignore
│
├── cloudsams                    # thin shim（`exec python -m cloudsams_tools "$@"`）
├── cloudsams_tools/             # === dispatcher + shared，零第三方 dep ===
│   ├── __init__.py
│   ├── __main__.py              # `python -m cloudsams_tools`
│   ├── cli.py                   # 頂層 dispatch：list / <tool> passthrough
│   ├── discovery.py             # 掃 tools/*/tool.yaml（唔 import tool）
│   └── lib/
│       ├── __init__.py
│       └── base.py              # §3 嘅 opt-in helpers（stdlib only）
│
├── tools/                       # === 每個 tool 一個 folder，互不 import ===
│   ├── _template/               # 複製呢個開新 tool
│   │   ├── README.md · tool.yaml · main.py · requirements.txt
│   ├── slp-split-pdf/
│   │   ├── README.md · tool.yaml · requirements.txt
│   │   ├── main.py              # run(argv) —— dispatcher entry
│   │   ├── split.py             # 核心邏輯（可獨立行、被 test import）
│   │   └── synthetic/           # fake fixture
│   └── class-photo-rename/      # 第二個 tool，示範點 fit 入 pattern
│       ├── README.md · tool.yaml · requirements.txt
│       └── main.py
│
└── tests/
    ├── requirements.txt
    ├── test_slp_split_pdf.py    # per-tool test（import tool 內部 module）
    └── test_discovery.py        # dispatcher / list 嘅 test（建議）
```

### 4.2 共用 utility 擺邊？—— 預設**唔共用**

**預設答案：唔好放喺任何共用位。** 一段 code 應該住喺**用緊佢嗰個 tool folder 入面**，直到有第二個 tool 真係要用。

- 一個 tool 內部要拆檔案 → 拆喺**自己 folder**（`tools/foo/parsing.py`、`tools/foo/render.py`）。tool 內部想點拆隨便，因為冇人由外面 import。
- 真係**兩個 tool 都要**、又 stable、又 domain-neutral（例：page-range 解析、safe-filename slug）→ 先升去 `cloudsams_tools/lib/`，加測試。

**唔准**開一個 `utils/` 大雜燴。`utils/` 會變成引力井：乜都掉入去、乜都互相 import，最後所有 tool 經 `utils/` 隱性耦合 —— 正正係 G2 想避免嘅嘢。唯一合法嘅共用位係 `cloudsams_tools/lib/`，而且有 §3.2 白名單守門。

**鐵律：`tools/a/` 永遠唔准 `import` `tools/b/` 嘅嘢。** 要共用 = 升 `lib/`（連同承擔穩定性責任），唔係橫向 import。

### 4.3 一個 tool 內部點拆模組

- **細 tool（一個 pass、<~150 行）**：一個 `main.py` 搞掂。`slp-split-pdf` 因為要保持 `split.py` 可被現有 test import，就 `main.py`（薄 entry）+ `split.py`（邏輯）兩個檔。
- **大 tool**：`main.py`（只做 argparse + 調度）+ 幾個 domain module（`parsing.py` / `boundary.py` …），全部住喺 tool folder 入面。
- 死板要求：`main.py` 保持薄 —— 佢係 adapter（argv → 業務函數），業務邏輯放去可測試嘅純函數。

### 4.4 依賴隔離

每個 tool **自己一個 `requirements.txt`**（pinned）。`slp-split-pdf` 用 `pypdf`，`class-photo-rename` 用 `pillow`，兩者互不知情。冇 root 級「全部 tool 嘅 mega-requirements」。裝邊個 tool 就裝邊個嘅 dep。Dispatcher core 唔靠任何一個。

---

## 5. Discoverability（Q5）：`cloudsams list` 讀 folder convention + manifest

### 5.1 揀咗：掃 folder + 讀靜態 manifest（唔讀 git、唔 import）

```
for d in tools/*/:
    if (d / "tool.yaml").exists():
        meta = parse_mini_yaml(d / "tool.yaml")
        yield ToolInfo(name=meta["name"], summary=..., status=..., runtime=...)
```

三個候選比較：

| 方案 | 判決 | 理由 |
|---|---|---|
| **讀 folder + manifest** ✅ | 揀 | 快、零 side-effect、唔使 import（缺 dep 都列到）、metadata 豐富（summary/status） |
| 讀 git metadata | 唔揀 | commit message／author 唔係 tool 用途；shallow clone / export 冇 `.git` 就散;慢 |
| import tool 攞 docstring | 唔揀 | 要 import → 觸發 tool 依賴、慢、一個壞 tool 拖冧 `list`（撞故障隔離） |

### 5.2 為何 manifest 用 flat mini-YAML，唔用 PyYAML / TOML

- 用 PyYAML → dispatcher core 多咗第三方 dep，`list` 喺乾淨 clone 行唔到（撞 §1.3.3）。
- `tomllib` 要 Python 3.11+，但 repo target 3.10+。
- Manifest 只係幾行 flat `key: value`，寫個 ~15 行 stdlib parser 就夠（見 `discovery.py`）。刻意犧牲 nested YAML 換取「零 dep、跨版本」。日後真係需要 nested 先再算。

### 5.3 `list` 輸出（示意）

```
$ cloudsams list
NAME              STATUS  RUNTIME  SUMMARY
slp-split-pdf     stable  python   Split CloudSAMS SLP PDF into per-page / per-range files
class-photo-rename beta   python   Rename class photos to CloudSAMS <class><regno> convention
```

實作 sketch 見 `cloudsams_tools/cli.py` + `cloudsams_tools/discovery.py`（呢兩個係全 repo 唯一有真邏輯嘅檔）。

---

## 6. 加一個新 tool —— step-by-step recipe

> 對應 G1：以下每一步都**唔 touch 任何共用檔案**。

1. `cp -r tools/_template tools/<your-tool>`（kebab-case 名）。
2. 改 `tools/<your-tool>/tool.yaml`：`name`（=folder 名）、`summary`、`status: wip`、`runtime`。
3. 喺 `main.py` 實作 `run(argv)`：argparse → 叫你嘅業務函數。想要共用 `--input/--output-dir`？`from cloudsams_tools.lib.base import add_common_io_args`（可選）。
4. 大 tool 就喺同 folder 拆多幾個 module；**唔准** import 其他 tool。
5. 寫 `requirements.txt`（pinned）；`synthetic/` 放 1–2 個假 fixture。
6. `tests/test_<tool>.py`：import 你 tool 內部純函數嚟測。
7. 跑 `cloudsams list` —— 應該即刻見到你個 tool，**冇改過任何中央檔案**。
8. 更新 `README.md` 個工具表（純文件，非必須為咗 CLI 運作）+ 開 PR（見 `CONTRIBUTING.md`）。

---

## 7. 改一個現有 tool —— 典型 workflow

1. 只喺 `tools/<tool>/` 入面改。問自己：**有冇 import `cloudsams_tools.lib`？** 有先至可能影響其他 tool。
2. 如果要改 `lib/` 入面嘅共用 helper：當佢係**公共 API**。跑晒**所有**用緊佢嘅 tool 嘅 test，唔淨係手頭嗰個。改 signature = breaking change，要更新所有 caller。
3. 加新依賴 → 改**自己** `requirements.txt`，唔 touch 其他 tool。
4. 純 tool 內部改（冇掂 `lib/`、冇改 `run()` signature、冇改 `tool.yaml` 嘅 `name`）→ 影響半徑 = 得嗰個 tool。呢個係常態，亦係 G2 想要嘅結果。
5. 跑 `tests/test_<tool>.py` + `cloudsams <tool> --help` sanity check。

---

## 8. `lib/` 收 vs 唔收 —— 一頁 guideline

**收（三個條件全中先收）：**
- ✅ **≥2 個 tool** 真係 import 緊（唔係「將來可能」）。
- ✅ **Stable**：signature 唔會月月變。
- ✅ **Domain-neutral**：page-range parse、safe-filename slug、common argparse、logging setup。唔綁 CloudSAMS 具體 schema。

**唔收：**
- ❌ 淨得一個 tool 用（住喺嗰個 tool folder）。
- ❌ 未定形、成日改（放喺 tool 內部先，穩定咗再升）。
- ❌ 業務／schema-specific 邏輯（某份 SLP PDF 嘅 layout heuristic）。
- ❌ 任何要拉第三方 dep 落 `cloudsams_tools/` core 嘅嘢（會整爛零-dep `list`）。

> 疑問時：**留喺 tool folder**。Duplication 平過 wrong abstraction；由 tool 升去 `lib/` 好易，由 `lib/` 拆返出嚟好痛。

---

## 9. Trade-offs（做咗咩取捨）

| 取咗 | 捨咗 | 點解值 |
|---|---|---|
| Auto-discovery dispatcher | 「一個 `argparse` subparser tree」嘅簡單感 | 換到零 registry + 故障隔離（G1+G2）；代價係 dispatch 邏輯自己寫（~1 個細檔） |
| Flat mini-YAML + 自寫 parser | PyYAML 嘅完整 YAML | 換到 core 零第三方 dep、`list` 喺乾淨 clone 行到；代價係唔支援 nested（暫時唔需要） |
| Convention `run(argv)` + 靜態 manifest | Python entry-points / plugin registry | 換到「開 folder 就得」嘅低 boilerplate；代價係冇 pip-installable console_scripts per tool |
| 預設唔共用、`lib/` 白名單守門 | 一個方便嘅 `utils/` | 換到 tool 之間唔會經 `utils/` 隱性耦合；代價係初期有少少 duplication |
| 每 tool 獨立 `requirements.txt` | 一個 root mega-requirements | 換到依賴隔離、裝邊個用邊個；代價係共用 dep 會列幾次 |
| Tool 雙模式（dispatcher + standalone） | 只准經 `cloudsams` 行 | 保住現有 `python split.py` + 現有 test 唔破；代價係 `main.py`/`split.py` 有少少 indirection |

### 未做（YAGNI，日後有需要先加）
- Node runtime 嘅實際 dispatch（`runtime: node` 已喺 manifest 預留，dispatcher 暫時只跑 python）。
- Nested manifest / capabilities 宣告。
- `cloudsams new <name>` scaffolding 指令（暫時 `cp -r _template` 就夠）。
- Per-tool 版本號、machine-readable `cloudsams list --json`（好易加：discovery 已回傳結構化 `ToolInfo`）。

---

## 10. 一頁總結

- **一個入口** `cloudsams`，**零中央 registry** —— 靠 runtime 掃 `tools/*/tool.yaml`。
- **Contract 得兩條**：`tool.yaml` + `main.py::run(argv)->int`。
- **Lazy import**：`list` 唔 import 任何 tool；`<tool>` 只 import 自己 —— 一個壞 tool 拖唔冧成個 CLI。
- **Core 零第三方 dep**：`list` 喺乾淨 clone 都行。
- **共用要守門**：預設住喺 tool folder，`lib/` 淨收「≥2 tool + stable + domain-neutral」；`tools/a` 永遠唔 import `tools/b`。
- **雙模式**：tool 照樣可以 `python split.py` 獨立行，唔破現有 test。
