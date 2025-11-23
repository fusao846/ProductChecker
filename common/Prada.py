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
from common.PutImage import put_image

import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np

RETRY_MAX = 3
RETRY_SLEEP = 5

SITE_DEFINE = [
    {
        "name":"Prada",
        "cookie_accept":{
            "By":By.CLASS_NAME,
            "name":"cta_accept"
        },
        "href_route":{
            "by":By.CLASS_NAME,
            "name":"product-card"
        },
        "paging":{
            "add_url":"/page/%PAGE%",
            "start_page":2
        },
        "reget_list":True,
        "colors":{
            
        }
    },
    {
        "name":"Prada0906",
        "cookie_accept":{
            "By":By.CLASS_NAME,
            "name":"cta_accept"
        },
        "href_route":{
            "by":By.CLASS_NAME,
            "name":"product-card"
        },
        "paging":{
            "add_url":"/page/%PAGE%",
            "start_page":2
        },
        "reget_list":True,
        "colors":{
            
        }
    },
]
def Scrape(
        driver, 
        options, 
        URL, 
        Log, 
        cg, 
        ws, 
        concat_size, 
        folder, 
        prefix,
        save_image_size,
        count_max,
        fileName,
        wb
    ):
    siteDefine = {}
    for sd in SITE_DEFINE:
        if sd["name"] == folder:
            siteDefine = sd
            break
    page = 0
    if siteDefine == {}:
        print(f"M1 サイト定義がありません {folder}")
        return
    if siteDefine["paging"]:
        page = siteDefine["paging"]["start_page"]
    
    listURL = URL
    product_count = 0
    liNo = 0
    prevHref = ""
    hrefs = []
    productNos = []
    
    while True:
        driver.get(listURL)  # 商品一覧ページURLに適宜変更
        time.sleep(5)
        wait = WebDriverWait(driver, 10)
        last_height = driver.execute_script("return document.body.scrollHeight")


        if siteDefine["cookie_accept"]:
            by = siteDefine["cookie_accept"]["By"]
            name = siteDefine["cookie_accept"]["name"]
            try:
                for i in [1,2,3,4,5]:
                    cookie_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((by, name))
                    )
                    if cookie_btn.is_displayed():
                        cookie_btn.click()
                        break
                    time.sleep(10)
            except Exception as e:
                print(e)
                Log.debug("商品一覧の再描画が間に合わなかった")


        lis = driver.find_elements(siteDefine["href_route"]["by"], siteDefine["href_route"]["name"])
        if len(lis) == 0:
            break 
        while True:
            if liNo >= len(lis):
                break
            li = lis[liNo]
            liChildren = li.find_elements(By.TAG_NAME, "a")
            if (len(liChildren) == 0):
                liNo += 1
                continue
            
            target = liChildren[0].get_attribute("href")
            targetDup = False
            for href in hrefs:
                if href["url"] == target:
                    targetDup = True
                    break
            if targetDup:
                Log.debug(f"same url {target}")
                liNo += 1
                continue
            hrefs.append({
                "url":target,
            })
            # LIS 再取得
            if siteDefine["reget_list"] == True:
                Log.debug(f"再取得前　lis len {len(lis)} liNo {liNo}")
                lis = driver.find_elements(siteDefine["href_route"]["by"], siteDefine["href_route"]["name"])
                Log.debug(f"再取得後　lis len {len(lis)}")
                liNewCnt = 0
                liFound = False
                for li in lis:
                    liChildren = li.find_elements(By.TAG_NAME, "a")
                    for anc in liChildren:
                        wkTarget = anc.get_attribute("href")
                        Log.debug(f"{liNewCnt} {wkTarget}")
                        if wkTarget == target:
                            Log.debug(f"found! {liNewCnt}")
                            liNo = liNewCnt
                            liFound = True
                            break
                    if liFound:
                        break
                    liNewCnt += 1
            liNo += 1
        Log.debug(f"total {product_count}")
        if siteDefine["paging"]:
            listURL = f"{URL}{siteDefine["paging"]["add_url"]}"
            listURL = listURL.replace("%PAGE%",f"{page}")
            print("M2 " + listURL)
            page += 1
        else:
            break
        #if page > 3:
        #    break
    
    productNo = ""
    colorName = ""
    description = ""
    numberOfPhoto = 0
    productName = ""
    productSeq = int(cg.getValue("inStartNo"))
    price = 0
    size = ""
    exLine = 2
    hrefCount = 0
    isCAP = False


    for href in hrefs:
        isCAP = False
        hrefCount += 1
        cg.setMessage("message", f"商品件数：{len(hrefs)} 処理件数：{hrefCount}\n")

        print(f"M4 {hrefCount} {href['url']}")
        productNo = ""
        colorName = ""
        description = ""
        numberOfPhoto = 0
        colorHref = ""
        price = 0
        size = ""

        driver.quit()
        driver = webdriver.Chrome(options=options)
        driver.get(href['url'])
        if siteDefine["cookie_accept"]:
            by = siteDefine["cookie_accept"]["By"]
            name = siteDefine["cookie_accept"]["name"]
            try:
                for i in [1,2,3,4,5]:
                    cookie_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((by, name))
                    )
                    if cookie_btn.is_displayed():
                        cookie_btn.click()
                        break
                    time.sleep(10)
            except Exception as e:
                print(e)
                Log.debug("商品一覧の再描画が間に合わなかった")

        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'h1[data-element="product-title"]')
            )
        )
        productName = title_element.text
        price_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'p[data-element="product-current-price"]')
        ))
        price = int(re.sub('[^0-9]', '',price_element.get_attribute('innerText')))
        print(f"M5 価格 {price}")
        colorPicker = driver.find_element(By.CLASS_NAME, "color-picker__wrapper")
        colorAnchors = colorPicker.find_elements(By.TAG_NAME, "a")
        print(f"M6 LEN:", len(colorAnchors))
        colorNames = []
        for colorAnchor in colorAnchors:
            time.sleep(2)
            try:
                colorHref = colorAnchor.get_attribute("href")
                print(f"M7 カラー選択:{colorAnchor.get_attribute('href')}")
            except:
                break
            print("M8 isdisplayed ",colorAnchor.is_displayed())  # 表示されているか
            print("M9 isenabled " ,colorAnchor.is_enabled())    # 有効か
            print("M10 loc into view " , colorAnchor.location_once_scrolled_into_view)  # 表示位置
            #input("COLOR BUTTON BEFORE CLICKING?続行するには Enter キーを押してください...")
            time.sleep(2)
            driver.execute_script("arguments[0].click();", colorAnchor)
            time.sleep(2)
            #input("COLOR BUTTON AFTER CLICKING?続行するには Enter キーを押してください...")
            # 詳細を見る
            #button = WebDriverWait(driver, 10).until(
            #    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '商品詳細')]"))
            #)
            #button.click()
            product_details_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-element="product-details"]')
                )
            )
            detail_p = product_details_div.find_element(By.TAG_NAME, "p")
            desc = detail_p.get_attribute('innerText')
            desc = f"<BR>{desc.replace('。','。<BR>')}"
            if desc.endswith("<BR>"):
                desc = desc[:-4] 
            lis = product_details_div.find_elements(By.TAG_NAME,'li')
            for li in lis:
                tx = li.get_attribute('innerText')
                if tx.startswith("商品品番"):
                    productNo = tx.split(":")[1].strip()
                desc += '<BR>' + tx
            description = desc
            # ×で閉じる
            #close_button = WebDriverWait(driver, 10).until(
            #    EC.element_to_be_clickable(
            #        (By.CSS_SELECTOR, 'button[aria-label="prspa_close_product_details"]')
            #    )
            #)
            #close_button.click()
            color_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//p[text()="カラー"]/following-sibling::p[1]')
                )
            )
            print(f"M11 ★COLOR ELE:{color_element.get_attribute("outerHTML")}")
            colorName = color_element.get_attribute("innerText")
            print(f"M12 COLOR:{colorName}")
            colorNames.append(colorName)
            img_elements = driver.find_elements(By.CSS_SELECTOR, 'img.pdp-product-img')

            images = []
            for img_element in img_elements:
                srcset = ""
                #print('----------')
                #print(f"M13 element {img_element.get_attribute('outerHTML')}")
                #print('----------')
                try:
                    srcset = img_element.get_attribute("srcset")
                    if srcset == "":
                        print("M14 ★srcset none")
                        srcset = img_element.get_attribute("data-srcset")
                        #print(f"M15 ★data-srcset {srcset}")
                except:
                    print("M16 ★srcset none")
                    srcset = img_element.get_attribute("data-srcset")
                    #print(f"M17 ★data-srcset {srcset}")
                # 例: srcset="url1, url2 2x, url3 3x"

                # カンマで分割して空白トリム
                candidates = [s.strip() for s in srcset.split(",")]
                #print(f"M18 ☆candidates:{candidates}")
                lastImage = candidates[len(candidates)-1]
                print(f"M19 ☆lastImage:{lastImage}")
                lastImageSplit = lastImage.split(" ")
                #print(f"M20 ☆lastImageSplit:{lastImageSplit}")
                images.append(lastImageSplit[0])
            Log.debug(f"M21 画像枚数:{len(images)}")
            print(images)
         
            no = 0
            for image in images:
                no = no + 1
                if no > 5:
                    break
                if image == '':
                    break
                numberOfPhoto = no
                image_url = image
                colorName2 = re.sub(r'[<>:"/\\|?*]', '_', colorName).rstrip(' .')
                productNo2 = re.sub(r'[<>:"/\\|?*]', '_', productNo).rstrip(' .')
                output_path = f"{folder}/image/{prefix.lower()}-{productSeq:04d}_{no}.jpg"
                print(f"M22 image_url:{image_url}")
                put_image(image_url, output_path, isCAP, save_image_size)
            try:
                Log.debug(f"商品ID:{prefix.upper()}-{productSeq:04d}")
                Log.debug(f"商品番号:{productNo}")
                Log.debug(f"商品名:{productName}")
                Log.debug(f"説明:{description}")
                Log.debug(f"価格:{price}")
                Log.debug(f"カラー:{colorName}")
                Log.debug(f"写真枚数:{numberOfPhoto}")
                Log.debug(f"C{exLine}")
                ws[f"B{exLine}"] = f"{prefix.upper()}-{productSeq:04d}"
                ws[f"C{exLine}"] = productName
                ws[f"G{exLine}"] = productNo
                ws[f"H{exLine}"] = colorName
                ws[f"I{exLine}"] = size
                ws[f"J{exLine}"] = description
                ws[f"K{exLine}"] = price
                ws[f"M{exLine}"] = numberOfPhoto
                ws[f"N{exLine}"] = colorHref
            except Exception as e:
                print("M23 EEERRRRRRRRRRRRRRRROOOOOOOOOOORRRRRRRRRRR!!!!!!!!!!!!!!!!!")
                print(e)
                time.sleep(1000)


            exLine += 1
            wb.save(fileName)
            colorMessage = ""
            ci = 0
            for cn in colorNames:
                if ci <= i:
                    colorMessage += f"{cn}✔ "
                else:
                    colorMessage += f"{cn}　 "
                ci += 1
            cg.setMessage("message", f"商品件数：{len(hrefs)} 処理件数：{hrefCount}\n{colorMessage}")

            productSeq += 1
           
    time.sleep(2)
    driver.quit()
    cg.setMessage("message", "終了しました")
    return

