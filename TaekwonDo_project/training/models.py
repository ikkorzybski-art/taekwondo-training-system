from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """Profil użytkownika"""
    BELT_CHOICES = [
        ('white', 'Biały'),
        ('yellow_white', 'Biało-żółty'),
        ('yellow', 'Żółty'),
        ('green_yellow', 'Żółto-zielony'),
        ('green', 'Zielony'),
        ('blue_green', 'Zielono-niebieski'),
        ('blue', 'Niebieski'),
        ('red_blue', 'Niebiesko-czerwony'),
        ('red', 'Czerwony'),
        ('black_red', 'Czerwono-czarny'),
        ('black_1', 'I Dan'),
        ('black_2', 'II Dan'),
        ('black_3', 'III Dan'),
        ('black_4', 'IV Dan'),
        ('black_5', 'V Dan'),
        ('black_6', 'VI Dan'),
        ('black_7', 'VII Dan'),
        ('black_8', 'VIII Dan'),
        ('black_9', 'IX Dan'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    belt_level = models.CharField(max_length=20, choices=BELT_CHOICES, default='white', verbose_name='Stopień pasa')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Telefon')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Data urodzenia')
    address = models.CharField(max_length=200, blank=True, verbose_name='Adres')
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name='Kontakt awaryjny')
    must_change_password = models.BooleanField(default=False, verbose_name='Wymagana zmiana hasła')
    temporary_password = models.CharField(max_length=255, blank=True, verbose_name='Hasło tymczasowe')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data rejestracji')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ostatnia aktualizacja')
    
class Meta:
        verbose_name = 'Profil użytkownika'
        verbose_name_plural = 'Profile użytkowników'
        ordering = ['user__username']
    
def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_belt_level_display()}"

# Automatyczne tworzenie profilu - tylko dla użytkowników tworzonych programowo
# NIE dla użytkowników z admina (admin używa inline)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Sprawdź czy profil już istnieje - jeśli tak, nie twórz nowego
    if created and not hasattr(instance, 'profile'):
        try:
            # Sprawdź czy profil już nie istnieje w bazie
            if not UserProfile.objects.filter(user=instance).exists():
                UserProfile.objects.create(user=instance)
        except:
            # Jeśli wystąpił błąd (np. profil już istnieje), ignoruj
            pass


class TrainingDay(models.Model):
    """Dni treningowe"""
    WEEKDAY_CHOICES = [
        (0, 'Poniedziałek'),
        (1, 'Wtorek'),
        (2, 'Środa'),
        (3, 'Czwartek'),
        (4, 'Piątek'),
    ]
    
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, verbose_name='Dzień tygodnia')
    start_time = models.TimeField(verbose_name='Godzina rozpoczęcia')
    end_time = models.TimeField(verbose_name='Godzina zakończenia')
    location = models.CharField(max_length=200, verbose_name='Lokalizacja')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='training_sessions', verbose_name='Instruktor')
    max_participants = models.IntegerField(default=30, verbose_name='Max uczestników')
    is_active = models.BooleanField(default=True, verbose_name='Aktywny')
    description = models.TextField(blank=True, verbose_name='Opis')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Dzień treningowy'
        verbose_name_plural = 'Dni treningowe'
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time}"

class Attendance(models.Model):
    """Rejestr obecności"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Użytkownik')
    training_day = models.ForeignKey(TrainingDay, on_delete=models.CASCADE, verbose_name='Dzień treningowy')
    date = models.DateField(default=timezone.now, verbose_name='Data')
    present = models.BooleanField(default=True, verbose_name='Obecny')
    notes = models.TextField(blank=True, verbose_name='Notatki')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   related_name='attendance_records', verbose_name='Dodane przez')
    
    class Meta:
        verbose_name = 'Obecność'
        verbose_name_plural = 'Obecności'
        ordering = ['-date', 'user__username']
        unique_together = ['user', 'training_day', 'date']
    
    def __str__(self):
        status = "✓" if self.present else "✗"
        return f"{status} {self.user.username} - {self.date}"

class Flashcard(models.Model):
    """Fiszki do nauki"""
    CATEGORY_CHOICES = [
        ('techniques', 'Techniki'),
        ('forms', 'Formy (Tul)'),
        ('terminology', 'Terminologia koreańska'),
        ('theory', 'Teoria'),
        ('history', 'Historia'),
        ('patterns', 'Wzorce ruchów'),
    ]
    
    # Grupy odpowiadające stopniom pasów
    GROUP_CHOICES = [
        ('white', 'Grupa Biały pas (10-9 kup)'),
        ('yellow', 'Grupa Żółty pas (8-7 kup)'),
        ('green', 'Grupa Zielony pas (6-5 kup)'),
        ('blue', 'Grupa Niebieski pas (4-3 kup)'),
        ('red', 'Grupa Czerwony pas (2-1 kup)'),
        ('black', 'Grupa Czarny pas (Dan)'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='Kategoria')
    question = models.TextField(verbose_name='Pytanie/Termin')
    answer = models.TextField(verbose_name='Odpowiedź/Definicja')
    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default='white', verbose_name='Grupa')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Utworzone przez')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    is_public = models.BooleanField(default=True, verbose_name='Publiczna')
    views_count = models.IntegerField(default=0, verbose_name='Liczba wyświetleń')
    
    class Meta:
        verbose_name = 'Fiszka'
        verbose_name_plural = 'Fiszki'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.question[:50]}"

class Quiz(models.Model):
    """Quizy"""
    title = models.CharField(max_length=200, verbose_name='Tytuł')
    description = models.TextField(verbose_name='Opis')
    category = models.CharField(max_length=50, choices=Flashcard.CATEGORY_CHOICES, verbose_name='Kategoria')
    time_limit = models.IntegerField(default=15, verbose_name='Limit czasu (minuty)')
    passing_score = models.IntegerField(default=70, verbose_name='Min. wynik do zaliczenia (%)')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Utworzony przez')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    is_active = models.BooleanField(default=True, verbose_name='Aktywny')
    attempts_count = models.IntegerField(default=0, verbose_name='Liczba prób')
    
    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizy'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class QuizQuestion(models.Model):
    """Pytania w quizie"""
    QUESTION_TYPES = [
        ('single', 'Jednokrotnego wyboru'),
        ('multiple', 'Wielokrotnego wyboru'),
        ('text', 'Odpowiedź opisowa'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Quiz')
    question_text = models.TextField(verbose_name='Treść pytania')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single', 
                                     verbose_name='Typ pytania')
    order = models.IntegerField(default=0, verbose_name='Kolejność')
    points = models.IntegerField(default=1, verbose_name='Punkty')
    text_answer = models.TextField(blank=True, null=True, 
                                   verbose_name='Oczekiwana odpowiedź (dla pytań opisowych)')
    
    class Meta:
        verbose_name = 'Pytanie quizu'
        verbose_name_plural = 'Pytania quizu'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Pytanie {self.order}"

class QuizAnswer(models.Model):
    """Odpowiedzi do pytań"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, 
                                related_name='answers', verbose_name='Pytanie')
    answer_text = models.CharField(max_length=500, verbose_name='Treść odpowiedzi')
    is_correct = models.BooleanField(default=False, verbose_name='Poprawna odpowiedź')
    
    class Meta:
        verbose_name = 'Odpowiedź'
        verbose_name_plural = 'Odpowiedzi'
    
    def __str__(self):
        return f"{self.answer_text[:50]} {'✓' if self.is_correct else '✗'}"

class QuizAttempt(models.Model):
    """Próby rozwiązania quizu"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Użytkownik')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name='Quiz')
    score = models.IntegerField(verbose_name='Wynik')
    total_questions = models.IntegerField(verbose_name='Liczba pytań')
    percentage = models.FloatField(verbose_name='Procent')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Rozpoczęty')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Zakończony')
    passed = models.BooleanField(default=False, verbose_name='Zaliczony')
    
    class Meta:
        verbose_name = 'Próba quizu'
        verbose_name_plural = 'Próby quizu'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.percentage:.0f}%)"


class UserQuizAnswer(models.Model):
    """Odpowiedzi użytkownika w quizie"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, 
                               related_name='user_answers', verbose_name='Próba')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, verbose_name='Pytanie')
    selected_answer = models.ForeignKey(QuizAnswer, on_delete=models.CASCADE, 
                                       null=True, blank=True, verbose_name='Wybrana odpowiedź')
    is_correct = models.BooleanField(default=False, verbose_name='Poprawna')
    
    class Meta:
        verbose_name = 'Odpowiedź użytkownika'
        verbose_name_plural = 'Odpowiedzi użytkowników'
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.user.username} - {self.question.text[:50]}"

class PrivateLesson(models.Model):
    """Zajęcia indywidualne z instruktorem"""
    STATUS_CHOICES = [
        ('available', 'Dostępne'),
        ('booked', 'Zarezerwowane'),
        ('completed', 'Zakończone'),
        ('cancelled', 'Anulowane'),
    ]
    
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, 
                                   related_name='instructor_lessons',
                                   verbose_name='Instruktor')
    student = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                null=True, blank=True,
                                related_name='student_lessons',
                                verbose_name='Uczeń')
    date = models.DateField(verbose_name='Data')
    start_time = models.TimeField(verbose_name='Godzina rozpoczęcia')
    end_time = models.TimeField(verbose_name='Godzina zakończenia')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default='available', verbose_name='Status')
    notes = models.TextField(blank=True, verbose_name='Notatki')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Zajęcia indywidualne'
        verbose_name_plural = 'Zajęcia indywidualne'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        student_name = self.student.get_full_name() if self.student else 'Wolny termin'
        return f"{self.date} {self.start_time} - {self.instructor.get_full_name()} ({student_name})"


class Exam(models.Model):
    """Terminy egzaminów na kolejne stopnie"""
    EXAM_TYPE_CHOICES = [
        ('color_belts', 'Pasy kolorowe (biało-żółty do czerwony)'),
        ('advanced_belts', 'Stopnie wyższe (czerwono-czarny do V Dan)'),
    ]
    
    BELT_CHOICES_COLOR = [
        ('yellow_white', 'Biało-żółty'),
        ('yellow', 'Żółty'),
        ('green_yellow', 'Żółto-zielony'),
        ('green', 'Zielony'),
        ('blue_green', 'Zielono-niebieski'),
        ('blue', 'Niebieski'),
        ('red_blue', 'Niebiesko-czerwony'),
        ('red', 'Czerwony'),
    ]
    
    BELT_CHOICES_ADVANCED = [
        ('black_red', 'Czerwono-czarny'),
        ('black_1', 'I Dan'),
        ('black_2', 'II Dan'),
        ('black_3', 'III Dan'),
        ('black_4', 'IV Dan'),
        ('black_5', 'V Dan'),
    ]
    
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default='color_belts', verbose_name='Typ egzaminu')
    date = models.DateField(verbose_name='Data egzaminu')
    time = models.TimeField(verbose_name='Godzina')
    location = models.CharField(max_length=200, verbose_name='Miejsce')
    examiner = models.CharField(max_length=200, blank=True, verbose_name='Egzaminator')
    max_participants = models.IntegerField(default=20, verbose_name='Maksymalna liczba uczestników')
    description = models.TextField(blank=True, verbose_name='Opis/Wymagania')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Egzamin'
        verbose_name_plural = 'Egzaminy'
        ordering = ['date', 'time']
    
    def __str__(self):
        return f"Egzamin {self.get_exam_type_display()} - {self.date}"
    
    def get_eligible_belts_display(self):
        """Zwraca listę pasów uprawnionych do egzaminu"""
        if self.exam_type == 'color_belts':
            return ', '.join([choice[1] for choice in self.BELT_CHOICES_COLOR])
        else:
            return ', '.join([choice[1] for choice in self.BELT_CHOICES_ADVANCED])