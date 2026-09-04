
## ⚠️ 部署路徑（2026-09-05 定案，8/17 事故後）

這個 repo 部署到**兩個地方**，push 之後要分別確認：

| 目的地 | 更新方式 |
|---|---|
| https://huangchingfeng.github.io/insurance-allinone/ | push 即自動 build（約 7 分鐘，別密集 push，會互相取消） |
| https://insurance.autolab.cloud/ （Cloudflare Pages） | **要另外跑** `06-dev-tools(開發工具)/24-cloudflare-pages-deploy(學員工具上架自動化)/deploy-tool.sh https://github.com/huangchingfeng/insurance-allinone.git insurance-allinone insurance` |

三條鐵律：

1. **改完必 commit ＋ push，再部署。** 不要從本機工作區直接 `wrangler pages deploy` ——
   8/17 就是這樣：本機落後上游 3 個 commit，擴充 242 題後直接部署，
   把 8/2 做的護欄整份洗掉，線上跑了 17 天沒護欄的版本才被發現。
2. **動手前先 `git fetch && git status`**，落後上游就先 pull。
3. 每週一 09:20 `com.afeng.sites-check` 會掃這個工作區：
   有未 commit 的檔、或落後上游，會寄警報到 ai@autolab.cloud。
