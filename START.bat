@echo off
title System Taekwon-Do
color 0B

echo.
echo  =============================================
echo          SYSTEM TAEKWON-DO
echo  =============================================
echo.
echo  Uruchamianie...
echo.

REM Przejdz do katalogu z plikiem .exe
cd /d "%~dp0dist"

REM Uruchom aplikacje
if exist "TaekwonDo_Serwer.exe" (
    start "" "TaekwonDo_Serwer.exe"
) else (
    echo BLAD: Nie znaleziono pliku TaekwonDo_Serwer.exe
    echo Upewnij sie, ze plik znajduje sie w folderze dist
    echo.
    pause
    exit /b 1
)

exit
