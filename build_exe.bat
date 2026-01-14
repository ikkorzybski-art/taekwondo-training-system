@echo off
REM Uruchom ten plik ręcznie aby zbudować pojedyncze .exe (nie uruchamia PyInstaller automatycznie)
REM Upewnij się, że masz zainstalowany pyinstaller w środowisku developerskim.

pyinstaller --onefile --noconsole ^
  --add-data "TaekwonDo_project;TaekwonDo_project" ^
  --add-data "TaekwonDo_project\training\templates;TaekwonDo_project\training\templates" ^
  --add-data "TaekwonDo_project\training\static;TaekwonDo_project\training\static" ^
  run_app.py

echo Build zakonczony. Sprawdz plik w folderze dist\run_app.exe
pause
