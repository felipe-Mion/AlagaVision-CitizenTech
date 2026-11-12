@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual ausente. Execute: py -m venv .venv
  echo Depois: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
mkdir resultados 2>nul
echo Analisando as tres fotos de cafe...
".venv\Scripts\python.exe" main.py --imagem data/fotos_cafe/cafe_01.png --liquido cafe --roi 270 705 378 1134 --max-cm 8 --atencao-cm 2 --critico-cm 5.5 --output resultados/cafe_01_analisada.jpg --csv resultados/cafe_01.csv --no-display
".venv\Scripts\python.exe" main.py --imagem data/fotos_cafe/cafe_02.png --liquido cafe --roi 205 804 393 1290 --max-cm 8 --atencao-cm 2 --critico-cm 5.5 --output resultados/cafe_02_analisada.jpg --csv resultados/cafe_02.csv --no-display
".venv\Scripts\python.exe" main.py --imagem data/fotos_cafe/cafe_03.png --liquido cafe --roi 342 762 518 1183 --max-cm 8 --atencao-cm 2 --critico-cm 5.5 --output resultados/cafe_03_analisada.jpg --csv resultados/cafe_03.csv --no-display
echo.
echo Fotos anotadas em resultados\cafe_XX_analisada.jpg
pause
