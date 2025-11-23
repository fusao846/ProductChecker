import os

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


def put_image(image_url, output_path, isCAP, save_image_size):

    # 画像をURLから取得
    response = requests.get(image_url)
    response.raise_for_status()  # エラーがあれば例外発生

    # 画像データをPillowで開く
    with Image.open(BytesIO(response.content)) as im:
        im = im.convert("RGB")  # JPEG用にRGBへ変換
        image_np = np.array(im)               # RGB形式（PillowはRGB順）
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)  # OpenCVはBGR順

        imsge_cv_orig = image_cv            
        image_cv, cropped = crop_below_face(image_cv, isCAP)
        if cropped == True:
            print(f"Cropped {output_path}")
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
            return image[0:y_end, :], True
        else:
            cut_y = y + int(h * 0.8)
            return image[cut_y:, :], True
    else:
        return image, False
