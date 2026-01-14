import os
import sys
from pathlib import Path

def main():
    # Jeśli aplikacja jest spakowana przez PyInstaller, pliki są wypakowywane do _MEIPASS
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent

    # Dodaj katalog projektu do sys.path
    sys.path.insert(0, str(base_path))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TaekwonDo_project.settings")

    # Ustaw working dir na folder zawierający manage.py
    manage_dir = base_path / "TaekwonDo_project"
    if (manage_dir / "manage.py").exists():
        os.chdir(manage_dir)

    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line([sys.argv[0], "runserver", "127.0.0.1:8000"])
    except Exception as e:
        print("Błąd uruchomienia aplikacji:", e)
        input("Naciśnij Enter aby zakończyć...")

if __name__ == "__main__":
    main()
