@echo off
set /p MSG=バックアップコメント：

:: 日付と時間を取得してフォーマットを整える
setlocal enabledelayedexpansion
for /f "tokens=2 delims==" %%A in ('"wmic os get localdatetime /value"') do set datetime=%%A

:: フォーマットをYYYY-MM-DD_HH-MM-SSに変換
set year=!datetime:~0,4!
set month=!datetime:~4,2!
set day=!datetime:~6,2!
set hour=!datetime:~8,2!
set minute=!datetime:~10,2!
set second=!datetime:~12,2!

set formattedDateTime=!year!-!month!-!day!_!hour!-!minute!-!second!

:: バックアップ先ファイル名の作成
set backupFileName=bk\!formattedDateTime!.zip

:: バックアップ処理
:: 例: フォルダをZIP形式でバックアップ

set destinationFolder=bk

if not exist "!destinationFolder!" mkdir "!destinationFolder!"

copy *.py bkwk
copy *.json bkwk
copy common\*.py bkwk\common
powershell compress-archive bkwk %backupFileName%

echo %backupFileName% %MSG% >> bk\bkupmemo.txt
echo done
pause
