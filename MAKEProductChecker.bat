SET PYTHONPATH=common

pyinstaller -w ProductChecker.py --onedir  --add-data "common;common" ^
--add-data "C:\Users\16015\AppData\Local\Programs\Python\Python312\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml;cv2/data"

rem pyinstaller ProductChecker.spec

xcopy config dist\ProductChecker\config /e /i /y
mkdir dist\ProductChecker\Loewe
mkdir dist\ProductChecker\Loewe\image
mkdir dist\ProductChecker\Log


pause