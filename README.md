auto-inline-booking
===============

用途
- 每日檢查 inline 訂位頁面，若發現「午餐時段」可選會嘗試自動為 2 人下訂（會盡量自動填寫聯絡資訊）。

快速開始（Windows PowerShell）
1. 建立並啟用 virtualenv
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. 安裝套件與 Playwright 瀏覽器
   ```powershell
   pip install -r requirements.txt
   python -m playwright install
   ```

3. 設定環境變數（示範）
   ```powershell
   $env:RES_NAME='張三'; $env:RES_PHONE='0912345678'; $env:RES_EMAIL='a@b.c'
   ```

4. 執行
   ```powershell
   python auto_inline_booking.py
   ```

排程（Windows Task Scheduler 範例）
- 建立一個每日觸發的工作，動作設為：
  程式：C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
  參數：
  -NoProfile -WindowStyle Hidden -Command "& { $env:RES_NAME='張三'; $env:RES_PHONE='0912345678'; cd 'C:\path\to\repo'; .\.venv\Scripts\Activate.ps1; python auto_inline_booking.py }"

注意事項與風險
- 若有 CAPTCHA、SMS/LINE 驗證或複雜動態 UI，腳本無法完全自動通過；會停下並需人工完成最後步驟。
- 請尊重網站使用條款與餐廳規定，避免過於頻繁的自動檢查造成封鎖。
- 若執行遇到 selector 找不到的情況，我可以協助你根據實際頁面 snapshot 調整 selector。
