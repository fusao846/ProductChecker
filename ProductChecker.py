import os
import sys
import re
import time
import json
import csv
import shutil
import threading
import random
import traceback
import importlib
 
from datetime import datetime,timedelta
from pprint import pprint
from openpyxl.styles import Alignment
from openpyxl.styles import Font
from openpyxl import load_workbook

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from common.Grids import CustomGrid, GRIDS as gr
from common.Log import Log

import Version

import common.Loewe
import common.Prada

import requests
from PIL import Image
from io import BytesIO

VERSION = Version.VERSION

class SITE_ITEM:
    DISPLAY_NAME = 0
    URL = 1
    FOLDER = 2
    SHEET = 3
    MODULE = 4
    PREFIX = 5
    IMAGE_SIZE = 6

def strtobool(b):
    if b.upper() == "TRUE":
        return True
    else:
        return False

def priceNumber(text, euro=False):
    if euro == True:
        text = text.replace('.','')
        text = text.replace(',','.')
       # print(f"Euro ver {text}")
    cleaned_text = re.sub(r"[^0-9.]", "", text)  # 数字以外の文字を削除
    print(f"cleaned_test [{cleaned_text}]")
    number = int(float(cleaned_text))  # 整数に変換
    return number

def remove_zeros(s):
    return re.sub(r'^0+(\d)', r'\1', s)

def concat_size(textEles):
    size = ""
    otherSizeCount = 0;
    cnt = 0
    for tx in textEles:
        t = tx.get_attribute("textContent").strip()
        if "通知" in t or "サイズを選ぶ" in t or "Notify" in t or t == "サイズ" or "在庫なし" in t:
            None
        else:
            t = t.replace(",", ".")
            tSplit = t.split(" ")
            if len(tSplit) > 1 and  "フランス" in tSplit[0]:
                t = tSplit[1].strip()
            else:
                t = tSplit[0].strip()
                if len(tSplit) > 1:
                    if tSplit[1] == "1/2":
                        t = t + ".5"
                    if tSplit[0] == "One" and tSplit[1] == "size":
                        t = "OneSize"
            
            t = t.replace("IT","")
            t = t.replace("UK","")
            t = t.replace(".0", "")
            if t == "0" or t == "00":
                None
            else:
                t = remove_zeros(t)
            if t in ["ミディアム" ,"ラージ","エクストララージ"]:
                otherSizeCount = otherSizeCount+1
            pattern = r'^[SLMX0-9.]+$'
            validSize = re.fullmatch(pattern, t)
            if size != "" and t != "" and validSize:
                size = size + "_"
            
            if validSize:
                size = size + t
    noZaiko = False
    if size == "" and otherSizeCount == 0:
        noZaiko = True
    if size == "" and otherSizeCount > 0:
        size = "OneSize"
    return size, noZaiko

CONFIG = {}
current = os.getcwd()
scraper = None
CHROME_FOLDER = "Chrome3"

STOP_FLAG = threading.Event()
thread = None

SITE_DEF = []
SELECTED_INDEX = 0

site_file = f"{current}\\config\\サイト定義.txt"
with open(site_file, newline='', encoding='utf-8') as s:
    reader = csv.reader(s)
    next(reader)
    for row in reader:
        SITE_DEF.append(row) 

print(SITE_DEF)

LOG = Log("\\log\\ProductChecker", True)
if getattr(sys, 'frozen', False):
    sys.stdout = open("log\\stdout.log", "w", encoding="utf-8")
    sys.stderr = open("log\\stderr.log", "w", encoding="utf-8")

LOG.put(f"Start version={VERSION}")
LOG.debug('init')
A=0
B=1
C=2
D=3
E=4
F=5
G=6
H=7
I=8
J=9
K=10
L=11
M=12

DEBUGGING=False
DEB = False
args = sys.argv
#if len(sys.argv) >= 2 and sys.argv[2] == "DEB":
#    DEB = True

def main():
    #print('★main')
    global CONFIG
    global LOG
    global DEB
    global thread
    global SITE_DEF
    global SELECTED_INDEX

    # 読み込み済みの写真の数をカウントする関数
    def count_photos(driver):
        return len(driver.find_elements(By.CSS_SELECTOR, "img"))  # 適宜セレクタを修正

    def OKClick(cg):
        # スクレイピングを別スレッドで開始
        errorMessage = cg.check()
        print(f"check result {errorMessage}")
        if errorMessage != "":
            cg.setMessage("message", errorMessage)
            return
        global thread
        STOP_FLAG.clear()
        thread = threading.Thread(target=OKClickMain, args=(cg,))
        thread.daemon = True  # メインスレッド終了時に自動終了
        thread.start()

    def OKClickMain(cg):
        global SITE_DEF
        global SELECTED_INDEX

        # Chrome起動
        options = webdriver.ChromeOptions()
        # options.add_argument("--start-maximized")
        service = Service()
        service.creation_flags = 0x08000000   
        options = Options()
        options.add_argument("--disable-speech-api")
        options.add_argument("--disable-features=MediaRouter,OptimizationHints,Translate,VoiceInteraction,WebSpeech")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-cache")
        options.add_argument("--no-sandbox")
        options.add_argument("--hide-scrollbars")
        options.add_argument(f"--window-position={0},{490}")
        options.add_argument("--window-size=1500,1024")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--log-level=3")
        
        driver = webdriver.Chrome(options=options)

        print(f"SELECTED_INDEX {SELECTED_INDEX}")
        module_name = SITE_DEF[SELECTED_INDEX][SITE_ITEM.MODULE]
        print(f"module_name {module_name}")
        wb = load_workbook("config\\商品情報.xlsx")
        ws = wb.active
        ws.title = SITE_DEF[SELECTED_INDEX][SITE_ITEM.SHEET]
        prefix = SITE_DEF[SELECTED_INDEX][SITE_ITEM.PREFIX]
        fileName = ""
        print('excel will save')
        try:
            fileName = f"{SITE_DEF[SELECTED_INDEX][SITE_ITEM.FOLDER]}\\商品情報.xlsx"
            wb.save(fileName)
        except:
            timestamp = datetime.now().strftime("%H%M%S")
            fileName = f"{SITE_DEF[SELECTED_INDEX][SITE_ITEM.FOLDER]}\\商品情報_{timestamp}.xlsx"
            wb.save(fileName)
        countMax = 0
        if len(sys.argv) > 1:
            countMax = int(sys.argv[1])
        module = common.Prada
        if module_name == "Loewe":
            module = common.Loewe
        
        module.Scrape(
            driver, 
            options, 
            SITE_DEF[SELECTED_INDEX][SITE_ITEM.URL], 
            LOG, 
            cg, 
            ws,
            concat_size,
            SITE_DEF[SELECTED_INDEX][SITE_ITEM.FOLDER],
            prefix,
            int(SITE_DEF[SELECTED_INDEX][SITE_ITEM.IMAGE_SIZE]),
            countMax,
            fileName,
            wb
        )

    def CancelClick(cg):
        LOG.debug("cancel")

    def ExitClick(cg):
        global scraper
        global thread
        result = cg.confirm("終了確認", "終了してもよろしいですか")
        if result:
            if scraper:
                STOP_FLAG.set()
                print("scraper quitting")
                scraper.quit()
                print("scraper done")

            if thread:
                if thread.is_alive():
                    print("thread alive")
                else:
                    print("thread done")

            if thread and thread.is_alive():
                thread.join()
            print("join done")
            LOG.debug("exit")
            cg.update()
            cg.destroy()
            sys.exit()
    def GoNext(cg):
        global DEBUGGING
        DEBUGGING = False
    def SiteSelect(cg, event):
        global SITE_DEF
        global SELECTED_INDEX
        print("SiteSelect callback")
        print(cg.getValue("inSite"))
        SELECTED_INDEX = cg.getSelectedIndex("inSite")
        cg.setReadOnlyValue("inURL", SITE_DEF[SELECTED_INDEX][1])
        cg.setReadOnlyValue("inFolder", SITE_DEF[SELECTED_INDEX][2])

    site_list = []
    for site in SITE_DEF:
        site_list.append(site[0])
    print(site_list)
    settings = {
        "title":"画像データ取得ツール",
        "width":800,
        "height":490,
        "left":5,
        "top":800,
        "grids":[
            {
                "type":gr.LABEL,
                "caption":f"画像データ取得ツール  {VERSION}"
            },
            {
                "type":gr.SELECT,
                "name":"inSite",
                "label":"サイト",
                "list":site_list,
                "onSelect":SiteSelect,
                "init":site_list[0],
            },
            {
                "type":gr.INPUT_READONLY,
                "name":"inURL",
                "label":"URL",
                "init":SITE_DEF[0][SITE_ITEM.URL],
                "readonly":True,
            },
            {
                "type":gr.INPUT_READONLY,
                "name":"inFolder",
                "label":"出力フォルダー",
                "init":SITE_DEF[0][SITE_ITEM.FOLDER],
                "readonly":True,
            },
            {
                "type":gr.INPUT,
                "name":"inStartNo",
                "label":"商品ID開始番号",
                "init":"0000",
                "readonly":False,
                "check":{
                    "require":True,
                    "numeric":True,
                    "max_length":4
                }
            },
            {
                "type":gr.BUTTONS,
                "buttons":[
                    {
                       "caption":"実行",
                        "callback":OKClick
                    },
                    {
                        "caption":"終了",
                        "callback":ExitClick
                    },
                ]
            },
            {
                "type":gr.MESSAGE,
                "name":"message",
                "lines":6,
            }
        ]
    }
    if DEB == True:
        settings["grids"][3]["buttons"].append(
            {
                "caption":"N",
                "callback":GoNext
            }
        )

    cg = CustomGrid(settings)

if __name__ == '__main__':

    main()
    