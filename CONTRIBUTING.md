# 加新 Tool

每個工具係 `tools/<tool-name>/` 入面一個獨立 folder。

> 詳細 step-by-step recipe（點樣加、點解噉設計）見 [ARCHITECTURE.md §6](./ARCHITECTURE.md#6-加一個新-tool--step-by-step-recipe)。

## 流程

1. **Spec**：用 `tools/_template/` 嘅 template 開新 folder。將「輸入／輸出／CLI 用法／sample fixture」寫入 `README.md`
2. **實作**：寫 script（Python 3.10+ 或 Node 18+）。冇雲端 call
3. **Fixture**：喺 `synthetic/` 放 1-2 個 fake 樣本 file 俾人試用。**唔好用真實 CloudSAMS export**
4. **本地測試**：確認 `tools/<tool>/README.md` 嘅「Quick Start」步驟由頭跑到尾 work
5. **PR**：開 PR 入 `main`，description 列明：(a) 解決乜問題 (b) input/output 格式 (c) sample run

## 結構要求

```
tools/<tool-name>/
├── README.md           # 必要 — Quick Start + 用法
├── split.py            # 或其他主 script
├── requirements.txt    # 或 package.json — pinned versions
├── synthetic/          # 1-2 個 fake fixture
│   └── README.md       # 解釋點樣整 fixture
└── .gitkeep            # 確保空 folder 都 tracked
```

## Naming

`tools/<tool-name>/` 嘅名要 kebab-case，例如：
- `slp-split-pdf` ✅
- `class-photo-rename` ✅
- `slp_split_pdf` ❌
- `SLP Split PDF` ❌

## 唔需要

- ❌ 任何 CI / GitHub Actions（暫時）
- ❌ 任何部署 / Pages
- ❌ 任何 database / ORM
- ❌ 任何 CloudSAMS API 連線
