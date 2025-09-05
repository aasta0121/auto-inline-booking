#!/usr/bin/env python3
# auto_inline_booking.py
# 每次執行會嘗試在 inline 頁面尋找可訂午餐時段並為 2 人下訂（盡可能自動填表）。
# 注意：若有 CAPTCHA、SMS/LINE 驗證或動態 UI，此腳本可能無法完全自動化最後一步，需要人工介入。

import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://inline.app/booking/-MXVFKXcHevGIxhpUJm5:inline-live-2/-MXVFKeEgsfOkYAkz6Xw?language=zh-tw"
HEADLESS = True
CHECK_DAYS_AHEAD = 30
WAIT_SHORT = 0.8
WAIT_LONG_MS = 8000

# 從環境變數讀取聯絡資訊
RES_NAME = os.getenv("RES_NAME", "")
RES_PHONE = os.getenv("RES_PHONE", "")
RES_EMAIL = os.getenv("RES_EMAIL", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def set_guests(page):
    try:
        # 嘗試常見 select
        sel = page.query_selector("select")
        if sel:
            try:
                page.select_option("select", value="2")
                logging.info("已設為 2 人 (select)。")
                return True
            except Exception:
                pass
        # 嘗試點擊含 '2 大' 或 '2位' 的元素
        for txt in ["2 大", "2位大人", "2位"]:
            locator = page.locator(f":text(\"{txt}\")").first
            if locator and locator.count() and locator.is_visible():
                locator.click()
                logging.info("已點選人數按鈕：%s", txt)
                return True
    except Exception as e:
        logging.debug("set_guests error: %s", e)
    logging.info("未能自動設定人數 (請手動確認)。")
    return False

def lunch_time_button(page):
    # 嘗試找含 12 的時段按鈕或明確含午餐文字的時間
    candidates = page.locator("button").all()
    for i in range(len(candidates)):
        try:
            txt = candidates[i].inner_text().strip()
        except Exception:
            continue
        if not txt:
            continue
        if "午餐" in txt or "12" in txt or "12:00" in txt or "12：00" in txt:
            # 返回 locator
            try:
                return candidates[i]
            except Exception:
                continue
    return None

def fill_and_submit(page):
    try:
        # 填 input
        inputs = page.query_selector_all("input")
        for inp in inputs:
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            name = (inp.get_attribute("name") or "").lower()
            if ("name" in placeholder or "姓名" in placeholder or "name" in name) and RES_NAME:
                inp.fill(RES_NAME)
            if ("phone" in placeholder or "手機" in placeholder or "tel" in name or "phone" in name) and RES_PHONE:
                inp.fill(RES_PHONE)
            if ("email" in placeholder or "信箱" in placeholder or "email" in name) and RES_EMAIL:
                inp.fill(RES_EMAIL)
        # 嘗試提交按鈕
        for txt in ["完成預訂", "送出", "確認預訂", "完成預約"]:
            btn = page.locator(f"button:has-text(\"{txt}\")").first
            try:
                if btn and btn.count() and btn.is_enabled():
                    btn.click()
                    logging.info("按下提交按鈕：%s", txt)
                    return True
            except Exception:
                continue
    except Exception as e:
        logging.debug("fill_and_submit error: %s", e)
    logging.info("未自動完成提交，可能需人工介入。")
    return False

def try_book_once():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()
        page.goto(URL, timeout=20000)
        logging.info("載入：%s", URL)
        time.sleep(WAIT_SHORT)
        set_guests(page)

        checked = 0
        visited = set()
        while checked < CHECK_DAYS_AHEAD:
            time.sleep(WAIT_SHORT)
            # 檢查午餐時段
            btn = lunch_time_button(page)
            if btn:
                logging.info("發現可能的午餐時段，嘗試點選。")
                try:
                    btn.click()
                except Exception:
                    try:
                        page.evaluate("(el) => el.click()", btn)
                    except Exception:
                        logging.warning("無法點選時段按鈕。")
                time.sleep(WAIT_SHORT)
                ok = fill_and_submit(page)
                if ok:
                    # 嘗試等待成功訊息
                    try:
                        page.wait_for_selector(":text(\"訂位成功\")", timeout=WAIT_LONG_MS)
                        logging.info("偵測到訂位成功訊息。")
                        context.close()
                        browser.close()
                        return True
                    except PWTimeout:
                        logging.info("未偵測到成功訊息，請檢查 LINE/SMS 等後續驗證。")
                        context.close()
                        browser.close()
                        return True
                else:
                    context.close()
                    browser.close()
                    return False

            # 若沒找到，嘗試點下一個日期按鈕（簡單 heuristic）
            advanced = False
            for b in page.query_selector_all("button"):
                try:
                    txt = (b.inner_text() or "").strip()
                except Exception:
                    continue
                if not txt or txt in visited:
                    continue
                if any(ch in txt for ch in ["年", "月", "日"]) and len(txt) < 40:
                    visited.add(txt)
                    try:
                        b.click()
                        logging.info("切換日期：%s", txt)
                        advanced = True
                        break
                    except Exception:
                        continue
            if not advanced:
                # 嘗試下一頁箭頭
                next_btn = page.locator("button[aria-label=\"Next\"], button:has-text(\"›\")").first
                if next_btn and next_btn.count() and next_btn.is_enabled():
                    try:
                        next_btn.click()
                        logging.info("翻頁")
                        advanced = True
                    except Exception:
                        pass
            if not advanced:
                logging.info("無法再翻頁或找到更多日期，結束檢查。")
                break
            checked += 1

        context.close()
        browser.close()
    return False

if __name__ == "__main__":
    logging.info("開始檢查與嘗試訂位 (2 人、午餐時段)")
    success = try_book_once()
    if success:
        logging.info("流程結束：已嘗試下訂或送出表單，請檢查手機/LINE/簡訊。")
    else:
        logging.info("流程結束：未找到午餐時段或未完成下訂。")
