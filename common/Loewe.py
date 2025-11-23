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

import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
def get_haarcascade_path():
    filename = "haarcascade_frontalface_default.xml"
    path = os.path.join(os.getcwd(), "config", filename)
    print(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} が存在しません")
    return path
face_cascade = cv2.CascadeClassifier(get_haarcascade_path())
if face_cascade.empty():
    print("❌ CascadeClassifier の読み込みに失敗しました")
else:
    print("✅ CascadeClassifier 読み込み成功")

# 顔の上から2/3をカットする関数
def crop_below_face(image, isCAP):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)  # 小さすぎる顔は無視
    )

    if len(faces) > 0:
        # 最初の顔だけ使う（複数ある場合）
        (x, y, w, h) = faces[0]

        if isCAP:
            y_end = y + int(h * 0.5)
            return image[0:y_end, :]
        else:
            cut_y = y + int(h * 0.8)
            return image[cut_y:, :]
    else:
        return image

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
    driver.get(URL)  # 商品一覧ページURLに適宜変更
    wait = WebDriverWait(driver, 10)
    last_height = driver.execute_script("return document.body.scrollHeight")

    try:
        for i in [1,2,3,4,5]:
            cookie_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            if cookie_btn.is_displayed():
                cookie_btn.click()
                break
            time.sleep(10)
    except:
        Log.debug("商品一覧の再描画が間に合わなかった")


    lis = driver.find_elements(By.TAG_NAME, "li")
    product_count = 0
    liNo = 0
    prevHref = ""
    hrefs = []
    productNos = []
    while True:
        cookie_btn = driver.find_elements(By.ID, "onetrust-accept-btn-handler")
        if len(cookie_btn) > 0:
            if cookie_btn[0].is_displayed():
                cookie_btn[0].click()
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
        #print(f"a found href={target}")
        if 'ja/loewe-x-on/women' in target: 
            prodDiv = li.find_elements(By.CLASS_NAME, 'product_info')
            if len(prodDiv) > 0:
                product_count = product_count + 1
                cg.setMessage("message", f"商品URL取得中 {product_count}")
                if count_max > 0:
                    if product_count >= count_max:
                        print('will break!')
                        break
                #print(target)
                if product_count % 4 == 1:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", li)
                    time.sleep(5)
                Log.debug(f"{product_count} {liNo} {prodDiv[0].get_attribute('innerText')} {target}")   
                prevHref = target
                tx = prodDiv[0].get_attribute('innerText').split('\n')
                tx1 = re.sub('[^0-9]', '', tx[1])
                hrefs.append({
                    "url":target,
                    "title":tx[0].strip(),
                    "price":int(tx1)
                })
                # LIS 再取得
                Log.debug(f"再取得前　lis len {len(lis)} liNo {liNo}")
                lis = driver.find_elements(By.TAG_NAME, "li")
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
    
    productNo = ""
    colorName = ""
    description = ""
    numberOfPhoto = 0
    productName = ""
    productSeq = int(cg.getValue("inStartNo"))
    price = ""
    size = ""
    exLine = 2
    hrefCount = 0
    isCAP = False
    for href in hrefs:
        isCAP = False
        hrefCount += 1
        cg.setMessage("message", f"商品件数：{len(hrefs)} 処理件数：{hrefCount}\n")
        productNo = ""
        colorName = ""
        description = ""
        numberOfPhoto = 0
        price = href["price"]
        size = ""

        driver.quit()
        driver = webdriver.Chrome(options=options)
        Log.debug(href['title'])
        Log.debug(href['price'])
        driver.get(href['url'])
        productName = href['title']
        if "キャップ" in productName:
            isCAP = True
        Log.debug(f"商品名：{productName}")
        time.sleep(1)
        time.sleep(2)
        divs = driver.find_elements(By.TAG_NAME, 'div')
        time.sleep(1)
        for div in divs:
            divText = div.get_attribute('innerText')
            if divText and 'モデルID' in divText:
                span = div.find_elements(By.TAG_NAME, 'span')
                if len(span) > 0:
                    productNo = span[0].get_attribute('innerText')
        ps = driver.find_elements(By.TAG_NAME, 'p')
        for p in ps:
            if p.get_attribute('innerText') == '色':
                clickOK = False
                cookie_btn = driver.find_elements(By.ID, "onetrust-accept-btn-handler")
                if len(cookie_btn) > 0:
                    if cookie_btn[0].is_displayed():
                        cookie_btn[0].click()

                for tryCount in [1,2,3,4,5]:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", p)
                        time.sleep(2)
                        p.click()
                        clickOK = True
                        break
                    except:
                        Log.debug('click failed')
                        time.sleep(5)
                if clickOK:
                    break
        
        colorTab = driver.find_elements(By.ID, 'color-tab')
        Log.debug(f"colorTab len {len(colorTab)}")
        colorHrefs = []
        colorNames = []
        if (len(colorTab) > 0):
            colorAnchors = colorTab[0].find_elements(By.TAG_NAME, 'a')
            colorButtons = colorTab[0].find_elements(By.TAG_NAME, 'button')
            for colorAnchor in colorAnchors:
                colorHrefs.append(colorAnchor.get_attribute('href'))
            for colorButton in colorButtons:
                colorNames.append(colorButton.get_attribute('innerText'))
        colorMessage = ""
        for cn in colorNames:
            colorMessage += f"{cn}　 "
        cg.setMessage("message", f"商品件数：{len(hrefs)} 処理件数：{hrefCount}\n{colorMessage}")

        for i, item in enumerate(colorHrefs):
            colorName = colorNames[i]
            Log.debug(f"カラー:{colorNames[i]}")
            driver.get(colorHrefs[i])
            images = []
            
            sizeTab = driver.find_elements(By.ID, 'sizes-tab')
            size = ''
            noZaiko = False
            if (len(sizeTab) > 0):
                sizeSpans = sizeTab[0].find_elements(By.TAG_NAME, 'span')
                size, noZaiko = concat_size(sizeSpans)
            else:
                size = 'OneSize'
            if noZaiko == True:
                Log.put(f"在庫なし {href['title']}")
                continue
            Log.debug(f"サイズ:{size}")
            
            detail_tab = driver.find_elements(By.ID, 'details-tab')
            if len(detail_tab) > 0:
                desc = ''
                ps = detail_tab[0].find_elements(By.TAG_NAME, 'p')
                if len(ps) > 0:
                    desc = ps[0].get_attribute('innerText')
                    desc = f"<BR>{desc.replace('。','。<BR>')}"
                if desc.endswith("<BR>"):
                    desc = desc[:-4] 
                lis = detail_tab[0].find_elements(By.TAG_NAME,'li')
                for li in lis:
                    tx = li.get_attribute('innerText')
                    desc += '<BR>' + tx
                divs = detail_tab[0].find_elements(By.TAG_NAME,'div')
                modelID = ''
                for div in divs:
                    spans = div.find_elements(By.TAG_NAME,'span')
                    if len(spans) == 2:     
                        desc += '<BR>' + spans[0].get_attribute('innerText') + ':' + spans[1].get_attribute('innerText')
                    if len(spans) == 1:     
                        modelID = '<BR>モデルID:' + spans[0].get_attribute('innerText')
                description = desc + modelID

            pictures = driver.find_elements(By.TAG_NAME,'picture')
            for picture in pictures:
                if "main-image-viewer" in picture.get_attribute('class'):
                    imgButtons = picture.find_elements(By.TAG_NAME, 'img')
                    if len(imgButtons) > 0:
                        images.append(imgButtons[0].get_attribute('src'))
                if len(images) >= 5:
                    break
            Log.debug(f"画像枚数:{len(images)}")
         
            no = 0
            for image in images:
                no = no + 1
                numberOfPhoto = no
                image_url = image
                colorName2 = re.sub(r'[<>:"/\\|?*]', '_', colorName).rstrip(' .')
                productNo2 = re.sub(r'[<>:"/\\|?*]', '_', productNo).rstrip(' .')
                output_path = f"{folder}/image/{prefix.lower()}-{productSeq:04d}_{no}.jpg"

                # 画像をURLから取得
                response = requests.get(image_url)
                response.raise_for_status()  # エラーがあれば例外発生

                # 画像データをPillowで開く
                with Image.open(BytesIO(response.content)) as im:
                    im = im.convert("RGB")  # JPEG用にRGBへ変換
                    image_np = np.array(im)               # RGB形式（PillowはRGB順）
                    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)  # OpenCVはBGR順
                    
                    image_cv = crop_below_face(image_cv, isCAP)
                    im = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
                    original_width, original_height = im.size
                    print(f"ORIGINAL {original_width} {original_height}")

                    image_size = 0
                    if save_image_size == 0:
                        image_size = max(original_width, original_height)
                    else:
                        image_size = save_image_size
                    print(f"image size: {image_size}")

                    if original_width > original_height:
                        new_width = image_size
                        new_height = int((image_size / original_width) * original_height)
                    else:
                        new_height = image_size
                        new_width = int((image_size / original_height) * original_width)
                    print(f"NEW {new_width} {new_height}")

                    resized_im = im.resize((new_width, new_height), Image.LANCZOS)

                    # 白背景を作成し中央に貼り付け
                    canvas = Image.new("RGB", (image_size, image_size), (255, 255, 255))
                    offset_x = (image_size - new_width) // 2
                    offset_y = (image_size - new_height) // 2
                    canvas.paste(resized_im, (offset_x, offset_y))
                    canvas.save(output_path, format="JPEG", quality=100)
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
            ws[f"N{exLine}"] = colorHrefs[i]
            wb.save(fileName)
            exLine += 1
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

