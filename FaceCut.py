import cv2
import mediapipe as mp
import numpy as np
import os
import glob

# Mediapipe の初期化
mp_face_detection = mp.solutions.face_detection

input_dir = "image"
output_dir = "croppedImage"
os.makedirs(output_dir, exist_ok=True)

# 顔の上から2/3をカットする関数
def crop_below_face(image):
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_detection.process(image_rgb)
        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            h, w = image.shape[:2]
            ymin = int(bbox.ymin * h)
            box_height = int(bbox.height * h)
            cut_y = ymin + int(box_height * 2 / 3)
            return image[cut_y:, :]
        else:
            return image  # 顔検出できない場合はそのまま

# 縦800ピクセルに拡大し、横に白パディングする
def resize_and_center_pad(image, height=800):
    h, w = image.shape[:2]
    scale = height / h
    new_h = height
    new_w = int(w * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 横が800より小さい場合、中央に白パディング
    if new_w < 800:
        pad_left = (800 - new_w) // 2
        pad_right = 800 - new_w - pad_left
        padded = cv2.copyMakeBorder(resized, 0, 0, pad_left, pad_right,
                                    cv2.BORDER_CONSTANT, value=(255, 255, 255))
    else:
        # 横が800以上になった場合はトリミング（中央800）
        x_start = (new_w - 800) // 2
        padded = resized[:, x_start:x_start + 800]
    return padded

# 日本語ファイル名対応で保存
def safe_imwrite(path, image):
    _, encoded = cv2.imencode('.jpg', image)
    with open(path, 'wb') as f:
        f.write(encoded)

# 画像処理の本体
jpg_files = glob.glob(os.path.join(input_dir, "*.jpg"))

for file_path in jpg_files:
    filename = os.path.basename(file_path)
    image = cv2.imdecode(np.fromfile(file_path, np.uint8), cv2.IMREAD_COLOR)

    if image is None:
        print(f"読み込み失敗: {filename}")
        continue

    cropped = crop_below_face(image)
    result = resize_and_center_pad(cropped, height=800)

    save_path = os.path.join(output_dir, filename)
    safe_imwrite(save_path, result)
    print(f"保存: {save_path}")
