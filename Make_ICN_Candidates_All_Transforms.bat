@echo off
setlocal EnableExtensions
title Make ICN candidates (all transforms)

cd /d "%~dp0"

if not exist "ps2icon_to_obj.exe"  echo [ERROR] ps2icon_to_obj.exe missing & goto :PAUSE
if not exist "obj_to_ps2icon.exe"  echo [ERROR] obj_to_ps2icon.exe missing & goto :PAUSE
for %%F in ("copy.icn" "del.icn" "list.icn") do if not exist %%~F echo [ERROR] Missing %%~nxF & set ERR=1
if defined ERR goto :PAUSE

set "DIR=out_stamped"
if not exist "%DIR%\" set "DIR=."

call :PickNewest "%DIR%" "copy_*.bmp"  BMP_COPY
if not defined BMP_COPY call :PickNewest "%DIR%" "copy*.bmp"  BMP_COPY
call :PickNewest "%DIR%" "list_*.bmp"  BMP_LIST
if not defined BMP_LIST call :PickNewest "%DIR%" "list*.bmp"  BMP_LIST
call :PickNewest "%DIR%" "delete_*.bmp" BMP_DEL
if not defined BMP_DEL call :PickNewest "%DIR%" "del_*.bmp"    BMP_DEL
if not defined BMP_DEL call :PickNewest "%DIR%" "delete*.bmp"  BMP_DEL
if not defined BMP_DEL call :PickNewest "%DIR%" "del*.bmp"     BMP_DEL

set ERR=
if not defined BMP_COPY echo [ERROR] No copy*.bmp found & set ERR=1
if not defined BMP_LIST echo [ERROR] No list*.bmp found & set ERR=1
if not defined BMP_DEL  echo [ERROR] No delete*/del*.bmp found & set ERR=1
if defined ERR goto :PAUSE

echo Using textures:
echo   copy.icn <- "%BMP_COPY%"
echo   del.icn  <- "%BMP_DEL%"
echo   list.icn <- "%BMP_LIST%"
echo.

set "WORK=_work_ps2icon"
set "OUT=_candidates"
if not exist "%WORK%" mkdir "%WORK%" >nul
for %%D in ("%OUT%\copy" "%OUT%\del" "%OUT%\list") do if not exist "%%~fD" mkdir "%%~fD" >nul

REM Extract each once
call :ExtractOBJ "copy.icn"  "%WORK%\copy.obj"  || goto :PAUSE
call :ExtractOBJ "del.icn"   "%WORK%\del.obj"   || goto :PAUSE
call :ExtractOBJ "list.icn"  "%WORK%\list.obj"  || goto :PAUSE

REM Build all 6 transforms per icon
for %%T in (none flipX flipY rot90 rot180 rot270) do (
  call :Make128Xform "%BMP_COPY%" "%WORK%\copy_%%T.bmp"  "%%T" || goto :PAUSE
  obj_to_ps2icon.exe -f "%WORK%\copy.obj" -t "%WORK%\copy_%%T.bmp" -o "%OUT%\copy\copy.%%T.icn" || (echo [ERROR] copy %%T & goto :PAUSE)
)
for %%T in (none flipX flipY rot90 rot180 rot270) do (
  call :Make128Xform "%BMP_DEL%" "%WORK%\del_%%T.bmp"  "%%T" || goto :PAUSE
  obj_to_ps2icon.exe -f "%WORK%\del.obj" -t "%WORK%\del_%%T.bmp" -o "%OUT%\del\del.%%T.icn" || (echo [ERROR] del %%T & goto :PAUSE)
)
for %%T in (none flipX flipY rot90 rot180 rot270) do (
  call :Make128Xform "%BMP_LIST%" "%WORK%\list_%%T.bmp"  "%%T" || goto :PAUSE
  obj_to_ps2icon.exe -f "%WORK%\list.obj" -t "%WORK%\list_%%T.bmp" -o "%OUT%\list\list.%%T.icn" || (echo [ERROR] list %%T & goto :PAUSE)
)

echo.
echo [OK] Candidates written to "%OUT%\copy", "%OUT%\del", "%OUT%\list".
echo Pick the exact one that renders correctly for each icon, then set it in transforms.cfg (next step).
:PAUSE
echo.
pause
exit /b 0

:PickNewest
setlocal
set "NEWEST="
for /f "delims=" %%F in ('dir /b /a:-d /o:-d "%~1\%~2" 2^>nul') do if not defined NEWEST set "NEWEST=%~1\%%F"
endlocal & set "%~3=%NEWEST%"
exit /b 0

:ExtractOBJ
REM %1 icn  %2 objOut
echo [EXTRACT] %~1
ps2icon_to_obj.exe -f "%~1" -o "%~2" || (echo [ERROR] extract failed: %~1 & exit /b 1)
exit /b 0

:Make128Xform
REM %1 in, %2 out, %3 transform
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Drawing;" ^
 "$in='%~1'; $out='%~2'; $tx='%~3'; $img=[Drawing.Image]::FromFile($in);" ^
 "try{ $bmp=New-Object Drawing.Bitmap 128,128; $g=[Drawing.Graphics]::FromImage($bmp);" ^
 "     $g.InterpolationMode='HighQualityBicubic'; $g.PixelOffsetMode='HighQuality'; $g.DrawImage($img,0,0,128,128); $g.Dispose();" ^
 "     switch (($tx+'').ToLower()) { 'flipx'{ $bmp.RotateFlip([Drawing.RotateFlipType]::RotateNoneFlipX) } 'flipy'{ $bmp.RotateFlip([Drawing.RotateFlipType]::RotateNoneFlipY) } 'rot90'{ $bmp.RotateFlip([Drawing.RotateFlipType]::Rotate90FlipNone) } 'rot180'{ $bmp.RotateFlip([Drawing.RotateFlipType]::Rotate180FlipNone) } 'rot270'{ $bmp.RotateFlip([Drawing.RotateFlipType]::Rotate270FlipNone) } default{} }" ^
 "     $bmp.Save($out,[Drawing.Imaging.ImageFormat]::Bmp); $bmp.Dispose() } finally { $img.Dispose() }" || exit /b 1
exit /b 0
