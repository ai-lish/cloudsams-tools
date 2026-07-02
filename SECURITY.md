# 安全守則

## ❌ 絕對唔可以 commit 入 repo

- 任何真實學生姓名、學號、家長聯絡資料
- 任何 CloudSAMS session cookie / API token / 登入 credentials
- 學校內部 URL 路徑或機密文件截圖
- 真實 CloudSAMS export 出嚟嘅 PDF / CSV / Excel（即使匿名化咗）

## ✅ 可以 commit

- 工具源碼（Python / Node / shell）
- 文件（README、設計筆記）
- 假資料 / synthetic fixture（用 `Ann Cheung`, `Ben Wong` 等明顯假名）
- 公開 PDF 規格文件

## 萬一唔小心 commit 咗

GitHub repo 對 public 嚟講，基本上 commit 過嘅嘢就要當永遠公開。即刻行動：
1. `git filter-repo` 或 BFG 重寫歷史
2. Rotate 所有相關 credentials
3. 知會校方（如涉及真實學生資料）

## 報告安全問題

呢個係公開 repository，唔接受 security reports。如發現誤 commit 機密資料，請直接喺 Discord #cloudsams thread 通知 Zachli。
