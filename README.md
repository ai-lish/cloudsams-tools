# CloudSAMS 行政小工具

香港中學校務系統 **CloudSAMS** 行政批量化工具集。每個工具一個獨立 folder，自己有 README + 依賴。

> ⚠️ **公開 repo**。請勿 commit 真實學生資料、學校內部 URL 或 CloudSAMS API credentials。詳見 [SECURITY.md](./SECURITY.md)。

## 工具列表

| Tool | 用途 | 狀態 |
|---|---|---|
| [slp-split-pdf](./tools/slp-split-pdf/) | SLP（學生學習概覽）PDF 批量分割 | ✅ v0.1 — 每頁一個 file |

## 設計原則

1. **零雲端依賴**：所有工具喺本機行，唔連 CloudSAMS server。Input file 由老師人手 export 之後先餵俾工具
2. **CLI-first**：每個工具都係 command-line script，唔需要 GUI 或 web server
3. **No student data in repo**：input/ output/ 永遠 gitignore。測試用 fixture 用 `synthetic/` + 假名
4. **單一職責**：一個 tool 一個 folder，唔好加其他功能入同一個 tool

## 加新 Tool

睇 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## License

未指定。預設 All Rights Reserved。如要重用請聯絡作者。
