# Skrypt do utworzenia skrótu START.bat z ikoną

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startBatPath = Join-Path $scriptDir "START.bat"
$shortcutPath = Join-Path $scriptDir "Uruchom Taekwon-Do.lnk"
$iconPath = Join-Path $scriptDir "TaekwonDo_project\training\static\images\tkd_icon.ico"

# Sprawdz czy START.bat istnieje
if (-not (Test-Path $startBatPath)) {
    Write-Host "BLAD: Nie znaleziono pliku START.bat" -ForegroundColor Red
    Read-Host "Nacisnij Enter aby zakonczyc"
    exit
}

# Utwórz obiekt WScript.Shell
$WScriptShell = New-Object -ComObject WScript.Shell

# Utwórz skrót
$Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $startBatPath
$Shortcut.WorkingDirectory = $scriptDir
$Shortcut.Description = "Uruchom System Zarządzania Treningami Taekwon-Do"

# Ustaw ikone jesli istnieje
if (Test-Path $iconPath) {
    $Shortcut.IconLocation = "$iconPath, 0"
    Write-Host "Ustawiono ikone: $iconPath" -ForegroundColor Green
} else {
    # Uzyj domyslnej ikony Windows dla plikow bat
    $Shortcut.IconLocation = "%SystemRoot%\System32\SHELL32.dll, 1"
    Write-Host "Nie znaleziono pliku .ico, uzyto domyslnej ikony" -ForegroundColor Yellow
}

# Zapisz skrót
$Shortcut.Save()

Write-Host ""
Write-Host "GOTOWE!" -ForegroundColor Green
Write-Host "Utworzono skrot: Uruchom Taekwon-Do.lnk" -ForegroundColor Cyan
Write-Host ""
Write-Host "Mozesz teraz:" -ForegroundColor White
Write-Host "  - Uzyc tego skrotu zamiast START.bat" -ForegroundColor Gray
Write-Host "  - Przeniesc skrot na pulpit" -ForegroundColor Gray
Write-Host "  - Skopiowac go do Menu Start" -ForegroundColor Gray
Write-Host ""

Read-Host "Nacisnij Enter aby zakonczyc"
