# Budowa pliku .exe (Windows)

Instrukcja jak ręcznie spakować aplikację Django do jednego pliku wykonywalnego przy użyciu PyInstaller.

WAŻNE: Ten repo zawiera skrypty i instrukcje — PyInstaller NIE jest uruchamiany automatycznie. Uruchom `build_exe.bat` ręcznie na maszynie deweloperskiej, jeśli chcesz zbudować .exe.

1) Zainstaluj zależności w środowisku developerskim:

```powershell
python -m pip install -r requirements.txt
```

2) Przygotuj statyczne pliki (opcjonalnie):

```powershell
python manage.py collectstatic --noinput
```

3) Uruchom skrypt budujący (ręcznie):

```powershell
.\\build_exe.bat
```

4) Po zakończeniu znajdziesz plik `dist\run_app.exe` — to pojedynczy plik wykonywalny. Możesz go skopiować na komputer bez Pythona i uruchomić bez instalacji środowiska.

Uwagi:
- `run_app.py` jest entrypointem; uruchomi lokalny serwer developerski Django na `http://127.0.0.1:8000`.
- Dla prostych dystrybucji lokalnych serwer developerski jest wystarczający; do środowisk produkcyjnych rozważ uruchomienie aplikacji za pomocą WSGI (np. `waitress`) lub hostingu.
- Jeśli brakują importy podczas budowy, uruchom PyInstaller z flagą `--hidden-import` lub utwórz plik `.spec`.

Jeśli chcesz, mogę przygotować plik `.spec` (nie uruchomię go) lub pomóc krok po kroku z budowaniem na Twojej maszynie.
