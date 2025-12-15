import subprocess
import webbrowser
import time
import sys
from pathlib import Path

def main():
    # Określ ścieżkę bazową
    if getattr(sys, 'frozen', False):
        # Jeśli uruchamiane jako .exe (PyInstaller)
        base_path = Path(sys.executable).parent.parent
    else:
        # Jeśli uruchamiane jako skrypt Python
        base_path = Path(__file__).parent
    
    # Ścieżki
    manage_py = base_path / "Nowy folder" / "TaekwonDo_project" / "manage.py"
    venv_python = base_path / "venv" / "Scripts" / "python.exe"
    
    print("===========================================")
    print("   SYSTEM ZARZĄDZANIA TRENINGAMI TAEKWON-DO")
    print("===========================================")
    print()
    print("Uruchamianie serwera...")
    print(f"Lokalizacja: {manage_py}")
    print()
    
    # Uruchom serwer Django
    try:
        process = subprocess.Popen(
            [str(venv_python), str(manage_py), "runserver"],
            cwd=manage_py.parent,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print("✓ Serwer uruchomiony!")
        print("Otwieranie przeglądarki...")
        
        # Poczekaj chwilę na uruchomienie serwera
        time.sleep(3)
        
        # Otwórz przeglądarkę
        webbrowser.open('http://127.0.0.1:8000')
        
        print()
        print("✓ Przeglądarka otwarta!")
        print()
        print("===========================================")
        print("  SERWER DZIAŁA NA: http://127.0.0.1:8000")
        print("===========================================")
        print()
        print("Aby zatrzymać serwer, zamknij okno konsoli Django.")
        print()
        input("Naciśnij Enter aby zakończyć...")
        
    except Exception as e:
        print(f"✗ BŁĄD: {e}")
        input("Naciśnij Enter aby zakończyć...")
        sys.exit(1)

if __name__ == "__main__":
    main()
