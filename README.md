# 歷史上的今天 Discord Bot

以 Python 3.11+ 與 discord.py 製作的繁體中文 Discord 機器人。可以查詢某一天的歷史事件、出生人物、逝世人物與節日，並設定每天自動發送至伺服器頻道。

資料來自中文維基百科的日期頁面，每則訊息附上來源連結。機器人會請求繁體中文版本；實際用字與資料完整度依維基百科頁面而定。連線或解析失敗時會顯示錯誤，不會編造歷史資料。

## 安裝與啟動

1. 安裝 Python 3.11 或更新版本。
2. 在 [Discord Developer Portal](https://discord.com/developers/applications) 建立應用程式，在 **Bot** 頁面建立機器人並取得 Token。Token 只填入本機 `.env`，請勿貼到聊天、提交至 Git 或放入公開檔案。
3. 在 **OAuth2 → URL Generator** 勾選 `bot` 與 `applications.commands`，機器人權限勾選 **View Channels**、**Send Messages**、**Embed Links**，用產生的網址將機器人邀請至伺服器。
4. 在專案資料夾建立虛擬環境並安裝套件：

```bash
python -m venv .venv
```

macOS／Linux：

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

編輯 `.env`，填入 `DISCORD_TOKEN`，然後啟動：

```bash
python -m history_bot
```

不需要啟用 Message Content 或其他 Privileged Gateway Intents。預設註冊全域斜線指令，Discord 可能需要一段時間才會顯示；開發時可設定 `DISCORD_GUILD_ID`，將指令快速註冊至指定的測試伺服器。

## 指令

| 指令 | 用途 |
| --- | --- |
| `/today` | 依預設時區查詢今天，預設列出 5 則歷史事件。 |
| `/today month:10 day:4 category:events count:5` | 查詢指定月日；不指定年份。 |
| `/daily channel:#歷史上的今天 hour:9 minute:0 timezone:Asia/Taipei category:events count:5` | 設定每天自動發送。只需指定 `channel`，其餘選項有預設值。 |
| `/daily-status` | 查看此伺服器目前的每日發送設定。 |
| `/daily-off` | 關閉此伺服器的每日發送。 |
| `/help` | 查看使用說明。 |

`category` 可選 `events`（事件）、`births`（出生）、`deaths`（逝世）、`holidays`（節日）；`count` 為 1–10，預設 5。指定日期時請同時填入 `month` 與 `day`。

`/daily`、`/daily-status`、`/daily-off` 僅限擁有 **管理伺服器（Manage Guild）** 權限的成員在伺服器內使用。每日發送目標須為一般文字頻道，機器人也必須擁有該頻道的查看、發送與嵌入連結權限。

每個伺服器有一組每日發送設定；重新執行 `/daily` 會更新設定。時間採 24 小時制，`hour` 為 0–23、`minute` 為 0–59，時區使用 IANA 名稱，例如 `Asia/Taipei`、`Asia/Hong_Kong` 或 `America/New_York`。

## 環境設定

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `DISCORD_TOKEN` | 必填 | Discord Bot Token。 |
| `DISCORD_GUILD_ID` | 留空 | 可選；開發時指定測試伺服器 ID。 |
| `DEFAULT_TIMEZONE` | `Asia/Taipei` | `/today` 與新增每日設定的預設時區。 |
| `DATABASE_PATH` | `data/history.db` | SQLite 資料庫，保存每日設定與發送日期。 |
| `LOG_LEVEL` | `INFO` | 記錄詳細程度，例如 `DEBUG`、`INFO`、`WARNING`。 |

每日排程約每 30 秒檢查一次。當天尚未發送且已過設定時間時會補發；因此在當日預定時間後啟動，也會發送今天的內容。成功發送後才保存當天紀錄，正常運作時每天發送一次。若程式在「訊息送出」與「紀錄寫入」之間中斷，重新啟動後可能重複發送。

更新 `/daily` 設定會保留最後成功發送日期，避免當天再次發送；`/daily-off` 會刪除設定及該日期紀錄。發送失敗會以 1 分鐘至 15 分鐘的間隔重試，成功後才寫入日期。若採用日光節約時間的時區，跳過的時間會在當天稍後補發，重複的時間仍只發送一次。

請只執行一個機器人程序，並保存 `DATABASE_PATH` 指向的資料庫；多個程序共用設定可能造成重複發送。要持續每日發送，需讓電腦或 VPS 保持運作，並讓機器人程序持續執行。

## 本機預覽與測試

離線預覽使用明確標示的示範資料，不需要 Discord Token：

```bash
python -m history_bot.preview --demo
```

使用維基百科實際資料預覽指定日期：

```bash
python -m history_bot.preview --month 10 --day 4
```

執行測試：

```bash
python -m unittest discover -s tests -v
```

專案另附 `requirements-lock.txt`，記錄這次驗證使用的完整套件版本。需要重現相同環境時，可改用 `pip install -r requirements-lock.txt`。

離線預覽與單元測試不代表已成功登入 Discord；實際登入與訊息發送需使用你自己的 Bot Token 與伺服器。

本次已通過 56 個離線測試，包括資料解析、快取與 HTTP 重試、Discord 指令與權限、日期邊界、排程競態及 SQLite 持久化。製作環境未提供 Discord Token，且網路政策未開放維基百科，因此尚未驗證真實 Discord 連線與維基百科 API 回應。

## 網路與維護

執行時需能連線至 `zh.wikipedia.org`（歷史資料）、`discord.com`（Discord REST API）及 `gateway.discord.gg`（WebSocket Gateway）。安裝套件需能存取 PyPI 與其套件下載主機；若使用限制網路的執行環境，請依環境規則開放必要連線。

Discord 連線會使用環境中的 `HTTPS_PROXY` 或 `HTTP_PROXY`，維基百科查詢也會遵循代理設定；保持 TLS 憑證驗證啟用。

備份時保存資料庫即可保留排程設定。分享原始碼或壓縮檔時，請排除 `.env`、虛擬環境與資料庫。若 Token 外洩，立即在 Developer Portal 的 Bot 頁面重設，再更新本機 `.env` 並重新啟動。
