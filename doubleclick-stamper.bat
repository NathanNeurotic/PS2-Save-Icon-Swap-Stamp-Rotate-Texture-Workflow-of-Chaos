@echo off
REM If you type a single space when prompted, it will texture-swap only.
set /p LABEL=Enter stamp text (or single space for texture-only): 
python stamp_like_example.py --box-file box.txt --text "%LABEL%" --images copy.bmp del.bmp delete.bmp list.bmp --output-dir out_stamped
echo Stamped textures are in out_stamped        pause
