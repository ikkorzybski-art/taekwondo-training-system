# System Treningowy Taekwon-Do 🥋

System do zarządzania treningami Taekwon-Do z funkcjami edukacyjnymi.

## Funkcje

- 👤 **System użytkowników**: Rejestracja, logowanie, profile z pasami
- 📚 **Fiszki edukacyjne**: Nauka technik i terminologii
- 📝 **Quizy**: Testy wiedzy z historią wyników i szczegółową analizą odpowiedzi
- 📊 **Statystyki**: Kompleksowy przegląd wyników z quizów
- 📅 **Dni treningowe**: Plan zajęć grupowych
- 👨‍🏫 **Zajęcia indywidualne**: Rezerwacja prywatnych lekcji
- ✅ **Obecności**: Śledzenie frekwencji
- 🎓 **Egzaminy**: Terminy egzaminów na pasy

## Technologie

- **Backend**: Django 5.2.9
- **Frontend**: Bootstrap 5.3.0, Font Awesome 6.4.0
- **Baza danych**: SQLite3
- **Python**: 3.14.0

## Instalacja

### 1. Sklonuj repozytorium
```bash
git clone https://github.com/twoja-nazwa/django-tkd.git
cd django-tkd
```

### 2. Utwórz środowisko wirtualne
```bash
python -m venv venv
```

### 3. Aktywuj środowisko
**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 5. Wykonaj migracje
```bash
cd TaekwonDo_project
python manage.py migrate
```

### 6. Utwórz superusera
```bash
python manage.py createsuperuser
```

### 7. Uruchom serwer
```bash
python manage.py runserver
```

Otwórz przeglądarkę pod adresem: http://127.0.0.1:8000/

## Panel administratora

Dostęp do panelu admina: http://127.0.0.1:8000/admin/

## Struktura projektu

```
django-tkd/
├── TaekwonDo_project/          # Wersja administracyjna
│   ├── manage.py
│   ├── db.sqlite3
│   ├── TaekwonDo_project/      # Ustawienia projektu
│   └── training/               # Główna aplikacja
│       ├── models.py           # Modele danych
│       ├── views.py            # Logika widoków
│       ├── urls.py             # Routing URL
│       ├── forms.py            # Formularze
│       ├── admin.py            # Konfiguracja panelu admina
│       ├── templates/          # Szablony HTML
│       └── static/             # Pliki statyczne (CSS)
├── Nowy folder/                # Wersja użytkownika
│   └── TaekwonDo_project/      # Struktura identyczna jak wyżej
└── venv/                       # Środowisko wirtualne (nie w repo)
```

## Modele danych

- **UserProfile**: Rozszerzenie użytkownika (pas, poziom)
- **TrainingDay**: Dni i godziny treningów
- **Attendance**: Obecności na treningach
- **Flashcard**: Fiszki edukacyjne
- **Quiz, QuizQuestion, QuizAnswer**: System quizów
- **QuizAttempt, UserQuizAnswer**: Historia wyników
- **PrivateLesson**: Zajęcia indywidualne
- **Exam**: Terminy egzaminów

## Licencja

Ten projekt jest prywatny i służy celom edukacyjnym.

## Autor

Projekt inżynierski - System treningowy Taekwon-Do
