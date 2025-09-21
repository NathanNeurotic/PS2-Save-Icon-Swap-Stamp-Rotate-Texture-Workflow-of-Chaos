@echo off
REM ============================================
REM Double-click to stamp text on list/copy/del
REM - Prompts for text
REM - Uses locked font path, placement, fit params
REM ============================================

cd /d "%~dp0"

REM Prompt user for text
set /p STAMP_TEXT=Enter the text to stamp: 

REM Run the Python script with locked options
python stamp_like_example.py ^
  --box-file box.txt ^
  --text "%STAMP_TEXT%" ^
  --images list.bmp copy.bmp delete.bmp ^
  --font "C:\Windows\Fonts\arialbd.ttf" ^
  --v-align middle --box-shift-y 90 ^
  --fit on --font-size 20 --fit-min 1 --fit-max 20 ^
  --stroke-width 1 --box-inset 0

echo.
echo Done! Output saved in "out_stamped"
pause
