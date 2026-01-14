import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, TrainingDay, Attendance, Flashcard, Quiz
from .forms import CustomUserCreationForm
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import csv
from datetime import datetime, timedelta

from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from .forms import ChangePasswordForm

from .models import (UserProfile, TrainingDay, Attendance, Flashcard, 
                     Quiz, QuizQuestion, QuizAnswer, QuizAttempt, PrivateLesson, UserQuizAnswer)
from .forms import (CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, 
                    TrainingDayForm, AttendanceForm, FlashcardForm)

# Helper function
def is_staff(user):
    return user.is_staff

# ===== REJESTRACJA I LOGOWANIE =====

@user_passes_test(is_staff)
def register_view(request):
    """Rejestracja użytkownika - TYLKO DLA ADMINA"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Sprawdź czy wygenerowano hasło
            if hasattr(user, '_generated_password'):
                messages.success(
                    request, 
                    f'✅ Użytkownik {user.username} został utworzony!<br>'
                    f'<strong>Login:</strong> {user.username}<br>'
                    f'<strong>Hasło tymczasowe:</strong> {user._generated_password}<br>'
                    f'<small>Użytkownik będzie musiał zmienić hasło przy pierwszym logowaniu.</small>',
                    extra_tags='safe'
                )
            else:
                messages.success(request, f'Użytkownik {user.username} został pomyślnie utworzony.')
            
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'training/register.html', {'form': form})

@ensure_csrf_cookie
def login_view(request):
    """Logowanie użytkownika"""
    if request.user.is_authenticated:
        return redirect('training:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Sprawdź czy użytkownik musi zmienić hasło
                if hasattr(user, 'profile') and user.profile.must_change_password:
                    messages.warning(
                        request, 
                        '⚠️ Musisz zmienić hasło przy pierwszym logowaniu. Zostaniesz przekierowany.'
                    )
                    return redirect('training:change_password')
                
                messages.success(request, f'Witaj ponownie, {user.first_name}!')
                next_url = request.GET.get('next', 'training:home')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'logins/login.html', {'form': form})

@login_required
def change_password_view(request):
    """Zmiana hasła (wymuszana przy pierwszym logowaniu)"""
    # Sprawdź czy użytkownik musi zmienić hasło
    if not request.user.profile.must_change_password:
        messages.info(request, 'Nie musisz zmieniać hasła.')
        return redirect('training:dashboard')
    
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Zaktualizuj sesję, aby użytkownik pozostał zalogowany
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            messages.success(request, '✅ Hasło zostało pomyślnie zmienione! Możesz teraz korzystać z systemu.')
            return redirect('training:dashboard')
    else:
        form = ChangePasswordForm(request.user)
        # Pokazz hasło tymczasowe w wiadomości pomocniczej
        if request.user.profile.temporary_password:
            messages.info(
                request, 
                f'Twoje hasło tymczasowe znajduje się w emailu od administratora.',
                extra_tags='safe'
            )
    
    return render(request, 'training/change_password.html', {'form': form})

@login_required
def logout_view(request):
    """Wylogowanie użytkownika"""
    logout(request)
    messages.info(request, 'Zostałeś wylogowany.')
    return redirect('training:home')

# ===== STRONA GŁÓWNA =====

def home(request):
    """Strona główna - dostępna dla wszystkich"""
    training_days = TrainingDay.objects.filter(is_active=True)
    
    context = {
        'training_days': training_days,
    }
    
    if request.user.is_authenticated:
        context['flashcards_count'] = Flashcard.objects.filter(is_public=True).count()
        context['quizzes_count'] = Quiz.objects.filter(is_active=True).count()
        
        # Statystyki użytkownika
        context['user_trainings'] = Attendance.objects.filter(
            user=request.user, present=True
        ).count()
        context['user_quizzes'] = QuizAttempt.objects.filter(
            user=request.user
        ).count()
    
    return render(request, 'training/home.html', context)

# ===== DASHBOARD =====

@login_required
def dashboard(request):
    """Panel użytkownika"""
    profile = request.user.profile
    
    # Statystyki
    total_trainings = Attendance.objects.filter(user=request.user, present=True).count()
    quiz_attempts = QuizAttempt.objects.filter(user=request.user)
    passed_quizzes = quiz_attempts.filter(passed=True).count()
    
    # Ostatnie aktywności
    recent_attendance = Attendance.objects.filter(user=request.user).order_by('-date')[:5]
    recent_quizzes = quiz_attempts.order_by('-started_at')[:5]
    
    context = {
        'profile': profile,
        'total_trainings': total_trainings,
        'quiz_attempts_count': quiz_attempts.count(),
        'passed_quizzes': passed_quizzes,
        'recent_attendance': recent_attendance,
        'recent_quizzes': recent_quizzes,
    }
    return render(request, 'training/dashboard.html', context)

# ===== PROFIL =====

@login_required
def profile_view(request):
    """Profil użytkownika"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil został zaktualizowany!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'training/profile.html', context)

# ===== DNI TRENINGOWE =====

def training_days_list(request):
    """Lista dni treningowych"""
    training_days = TrainingDay.objects.filter(is_active=True)
    return render(request, 'training/training_days.html', {'training_days': training_days})

@user_passes_test(is_staff)
def training_day_create(request):
    """Dodawanie dnia treningowego"""
    if request.method == 'POST':
        form = TrainingDayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dzień treningowy został dodany!')
            return redirect('training_days_list')
    else:
        form = TrainingDayForm()
    
    return render(request, 'training/training_day_form.html', {'form': form, 'action': 'Dodaj'})

@user_passes_test(is_staff)
def training_day_edit(request, pk):
    """Edycja dnia treningowego"""
    training_day = get_object_or_404(TrainingDay, pk=pk)
    
    if request.method == 'POST':
        form = TrainingDayForm(request.POST, instance=training_day)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dzień treningowy został zaktualizowany!')
            return redirect('training_days_list')
    else:
        form = TrainingDayForm(instance=training_day)
    
    return render(request, 'training/training_day_form.html', {
        'form': form, 
        'action': 'Edytuj',
        'training_day': training_day
    })

@user_passes_test(is_staff)
def training_day_delete(request, pk):
    """Usuwanie dnia treningowego"""
    training_day = get_object_or_404(TrainingDay, pk=pk)
    training_day.delete()
    messages.success(request, 'Dzień treningowy został usunięty!')
    return redirect('training_days_list')

# ===== OBECNOŚĆ =====

@login_required
def attendance_list(request):
    """Lista obecności"""
    if request.user.is_staff:
        attendances = Attendance.objects.select_related('user', 'training_day').all()
    else:
        attendances = Attendance.objects.filter(user=request.user)
    
    # Filtrowanie
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_filter = request.GET.get('user')
    
    if date_from:
        attendances = attendances.filter(date__gte=date_from)
    if date_to:
        attendances = attendances.filter(date__lte=date_to)
    if user_filter and request.user.is_staff:
        attendances = attendances.filter(user__username__icontains=user_filter)
    
    # Statystyki
    total_present = attendances.filter(present=True).count()
    total_absent = attendances.filter(present=False).count()
    
    context = {
        'attendances': attendances[:50],  # Limit 50 wyników
        'total_present': total_present,
        'total_absent': total_absent,
    }
    return render(request, 'training/attendance_list.html', context)

@user_passes_test(is_staff)
def attendance_create(request):
    """Dodawanie obecności"""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.created_by = request.user
            attendance.save()
            messages.success(request, 'Obecność została zapisana!')
            return redirect('attendance_list')
    else:
        form = AttendanceForm()
    
    return render(request, 'training/attendance_form.html', {'form': form})

@user_passes_test(is_staff)
def attendance_export_csv(request):
    """Export obecności do CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="obecnosc.csv"'
    response.write('\ufeff')  # BOM dla polskich znaków
    
    writer = csv.writer(response)
    writer.writerow(['Użytkownik', 'Imię', 'Nazwisko', 'Data', 'Dzień treningowy', 
                     'Obecny', 'Notatki', 'Dodane przez'])
    
    attendances = Attendance.objects.select_related('user', 'training_day', 'created_by').all()
    
    for att in attendances:
        writer.writerow([
            att.user.username,
            att.user.first_name,
            att.user.last_name,
            att.date.strftime('%Y-%m-%d'),
            str(att.training_day),
            'Tak' if att.present else 'Nie',
            att.notes,
            att.created_by.username if att.created_by else ''
        ])
    
    return response

# ===== FISZKI =====

@login_required
def flashcards_list(request):
    """Lista fiszek"""
    category = request.GET.get('category', '')
    group = request.GET.get('group', '')
    
    flashcards = Flashcard.objects.filter(
        Q(is_public=True) | Q(created_by=request.user)
    )
    
    if category:
        flashcards = flashcards.filter(category=category)
    if group:
        flashcards = flashcards.filter(group=group)
    
    flashcards = flashcards.order_by('-created_at')
    
    context = {
        'flashcards': flashcards,
        'categories': Flashcard.CATEGORY_CHOICES,
        'groups': Flashcard.GROUP_CHOICES,
    }
    return render(request, 'training/flashcards.html', context)

@login_required
def flashcard_create(request):
    """Dodawanie fiszki"""
    if request.method == 'POST':
        form = FlashcardForm(request.POST)
        if form.is_valid():
            flashcard = form.save(commit=False)
            flashcard.created_by = request.user
            flashcard.save()
            messages.success(request, 'Fiszka została dodana!')
            return redirect('training:flashcards_list')
    else:
        form = FlashcardForm()
    
    return render(request, 'training/flashcard_form.html', {'form': form})

# ===== QUIZY =====

@login_required
def quiz_list(request):
    """Lista quizów"""
    quizzes = Quiz.objects.filter(is_active=True).annotate(
        questions_count=Count('questions')
    )
    
    for quiz in quizzes:
        quiz.user_attempts = QuizAttempt.objects.filter(
            user=request.user, quiz=quiz
        ).order_by('-started_at')[:3]
    
    return render(request, 'training/quiz_list.html', {'quizzes': quizzes})

@login_required
def quiz_take(request, pk):
    """Rozwiązywanie quizu"""
    quiz = get_object_or_404(Quiz, pk=pk, is_active=True)
    questions = quiz.questions.prefetch_related('answers').all()
    
    # Sprawdź czy użytkownik już rozwiązał ten quiz
    latest_attempt = QuizAttempt.objects.filter(
        user=request.user, 
        quiz=quiz,
        completed_at__isnull=False
    ).order_by('-completed_at').first()
    
    # Jeśli jest ukończona próba i użytkownik nie zażądał ponowienia (retry=1), przekieruj do wyników
    retry = request.GET.get('retry')

    # DEBUG: logujemy kto i co żąda — pomocne przy problemach z przekierowaniem
    try:
        print(f"DEBUG quiz_take: user={{request.user.username if request.user.is_authenticated else request.user}}, authenticated={{request.user.is_authenticated}}, latest_attempt_id={{latest_attempt.id if latest_attempt else None}}, retry={{retry}}")
    except Exception as e:
        print('DEBUG quiz_take: failed to print debug info', e)

    if latest_attempt and retry != '1':
        print(f"DEBUG quiz_take: redirecting to result, attempt_id={{latest_attempt.id}}")
        return redirect('training:quiz_result', pk=pk, attempt_id=latest_attempt.id)
    else:
        print('DEBUG quiz_take: allowing attempt (retry requested or no previous attempt)')
    
    if request.method == 'POST':
        score = 0
        total = questions.count()
        
        # Utwórz próbę
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=0,  # Zaktualizujemy później
            total_questions=total,
            percentage=0,  # Zaktualizujemy później
            completed_at=timezone.now(),
            passed=False  # Zaktualizujemy później
        )
        
        # Zapisz odpowiedzi użytkownika
        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            selected_answer = None
            is_correct = False
            
            if selected_answer_id:
                try:
                    selected_answer = QuizAnswer.objects.get(id=selected_answer_id)
                    is_correct = selected_answer.is_correct
                    if is_correct:
                        score += 1
                except QuizAnswer.DoesNotExist:
                    pass
            
            # Zapisz odpowiedź użytkownika
            UserQuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct
            )
        
        # Zaktualizuj wynik próby
        percentage = (score / total * 100) if total > 0 else 0
        passed = percentage >= quiz.passing_score
        
        attempt.score = score
        attempt.percentage = percentage
        attempt.passed = passed
        attempt.save()
        
        # Aktualizuj licznik prób
        quiz.attempts_count += 1
        quiz.save()
        
        messages.success(request, f'Quiz zakończony! Wynik: {score}/{total} ({percentage:.0f}%)')
        return redirect('training:quiz_result', pk=pk, attempt_id=attempt.id)
    
    return render(request, 'training/quiz_take.html', {
        'quiz': quiz,
        'questions': questions,
    })

@login_required
def quiz_result(request, pk, attempt_id):
    """Wyniki quizu z szczegółami odpowiedzi"""
    quiz = get_object_or_404(Quiz, pk=pk)
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user, quiz=quiz)
    
    # Pobierz wszystkie próby użytkownika dla tego quizu
    attempts = QuizAttempt.objects.filter(
        user=request.user, quiz=quiz
    ).order_by('-started_at')
    
    # Pobierz odpowiedzi użytkownika dla tej próby
    user_answers = attempt.user_answers.select_related(
        'question', 'selected_answer'
    ).prefetch_related('question__answers').all()
    
    # Przygotuj dane pytań z odpowiedziami
    questions_data = []
    for user_answer in user_answers:
        question = user_answer.question
        all_answers = question.answers.all()
        correct_answer = all_answers.filter(is_correct=True).first()
        
        questions_data.append({
            'question': question,
            'user_answer': user_answer.selected_answer,
            'correct_answer': correct_answer,
            'is_correct': user_answer.is_correct,
            'all_answers': all_answers
        })
    
    # Statystyki
    if attempts.exists():
        best_score = attempts.order_by('-percentage').first()
        avg_score = sum(a.percentage for a in attempts) / attempts.count()
    else:
        best_score = None
        avg_score = 0
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'questions_data': questions_data,
        'attempts': attempts,
        'best_score': best_score,
        'avg_score': avg_score,
    }
    return render(request, 'training/quiz_result.html', context)
    
    # Statystyki
    if attempts.exists():
        best_score = attempts.order_by('-percentage').first()
        avg_score = sum(a.percentage for a in attempts) / attempts.count()
    else:
        best_score = None
        avg_score = 0
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
        'best_score': best_score,
        'avg_score': avg_score,
    }
    return render(request, 'training/quiz_result.html', context)

def index(request):
    """Widok index - przekierowanie na stronę główną"""
    from django.shortcuts import redirect
    return redirect('training:home')

# ===== ZAJĘCIA INDYWIDUALNE (ADMIN) =====

@user_passes_test(is_staff)
def manage_private_lessons(request):
    """Zarządzanie zajęciami indywidualnymi - TYLKO DLA ADMINA"""
    # Pobierz wszystkie zajęcia
    all_lessons = PrivateLesson.objects.all().select_related('instructor', 'student').order_by('date', 'start_time')
    
    # Pobierz instruktorów (użytkownicy będący staff)
    instructors = User.objects.filter(is_staff=True)
    
    # Statystyki
    available_count = PrivateLesson.objects.filter(status='available').count()
    booked_count = PrivateLesson.objects.filter(status='booked').count()
    completed_count = PrivateLesson.objects.filter(status='completed').count()
    
    context = {
        'lessons': all_lessons,
        'instructors': instructors,
        'available_count': available_count,
        'booked_count': booked_count,
        'completed_count': completed_count,
    }
    return render(request, 'training/manage_private_lessons.html', context)

@user_passes_test(is_staff)
@require_http_methods(["POST"])
def generate_weekly_lessons(request):
    """Dodaje pojedynczy termin zajęć indywidualnych"""
    instructor_id = request.POST.get('instructor_id')
    weekday = request.POST.get('weekday')
    start_time_str = request.POST.get('start_time', '17:00')
    end_time_str = request.POST.get('end_time', '18:00')
    
    if not instructor_id:
        messages.error(request, 'Wybierz instruktora!')
        return redirect('training:manage_private_lessons')
    
    if not weekday:
        messages.error(request, 'Wybierz dzień tygodnia!')
        return redirect('training:manage_private_lessons')
    
    instructor = get_object_or_404(User, id=instructor_id, is_staff=True)
    
    # Parsuj godziny
    from datetime import time
    start_time = time(*map(int, start_time_str.split(':')))
    end_time = time(*map(int, end_time_str.split(':')))
    
    # Oblicz najbliższą datę dla wybranego dnia tygodnia
    today = timezone.now().date()
    target_weekday = int(weekday)
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    lesson_date = today + timedelta(days=days_ahead)
    
    # Sprawdź limit 5 zajęć na dzień dla instruktora
    lessons_on_date = PrivateLesson.objects.filter(
        instructor=instructor,
        date=lesson_date
    ).count()
    
    if lessons_on_date >= 5:
        weekday_names = {1: 'wtorek', 2: 'środę', 3: 'czwartek'}
        messages.error(request, f'Osiągnięto maksymalny limit 5 zajęć indywidualnych na {weekday_names[target_weekday]} {lesson_date.strftime("%d.%m.%Y")} dla tego instruktora!')
        return redirect('training:manage_private_lessons')
    
    # Sprawdź czy już istnieje
    existing = PrivateLesson.objects.filter(
        instructor=instructor,
        date=lesson_date,
        start_time=start_time,
        end_time=end_time
    ).exists()
    
    if existing:
        messages.warning(request, 'Ten termin już istnieje!')
        return redirect('training:manage_private_lessons')
    
    # Utwórz termin
    PrivateLesson.objects.create(
        instructor=instructor,
        date=lesson_date,
        start_time=start_time,
        end_time=end_time,
        status='available'
    )
    
    weekday_names = {1: 'wtorek', 2: 'środę', 3: 'czwartek'}
    messages.success(request, f'Dodano termin zajęć na {weekday_names[target_weekday]} {lesson_date.strftime("%d.%m.%Y")} o {start_time.strftime("%H:%M")}!')
    return redirect('training:manage_private_lessons')

@user_passes_test(is_staff)
@require_http_methods(["POST"])
def delete_private_lesson(request, lesson_id):
    """Usuwa termin zajęć indywidualnych"""
    lesson = get_object_or_404(PrivateLesson, id=lesson_id)
    
    if lesson.status == 'booked':
        messages.error(request, 'Nie można usunąć zarezerwowanych zajęć! Anuluj rezerwację lub oznacz jako ukończone.')
        return redirect('training:manage_private_lessons')
    
    lesson.delete()
    messages.success(request, 'Termin zajęć został usunięty.')
    return redirect('training:manage_private_lessons')

@user_passes_test(is_staff)
@require_http_methods(["POST"])
def mark_lesson_completed(request, lesson_id):
    """Oznacza zajęcia jako ukończone"""
    lesson = get_object_or_404(PrivateLesson, id=lesson_id)
    lesson.status = 'completed'
    lesson.save()
    messages.success(request, 'Zajęcia oznaczono jako ukończone.')
    return redirect('training:manage_private_lessons')


# ===== QUIZY =====

@login_required
def quiz_list(request):
    """Lista quizów"""
    quizzes = Quiz.objects.filter(is_active=True).annotate(
        questions_count=Count('questions')
    )
    
    for quiz in quizzes:
        quiz.user_attempts = QuizAttempt.objects.filter(
            user=request.user, quiz=quiz
        ).order_by('-started_at')[:3]
    
    return render(request, 'training/quiz_list.html', {'quizzes': quizzes})

@login_required
@login_required
def quiz_take(request, pk):
    """RozwiÄ…zywanie quizu"""
    quiz = get_object_or_404(Quiz, pk=pk, is_active=True)
    questions = quiz.questions.prefetch_related('answers').all()
    
    # SprawdĹş czy uĹĽytkownik juĹĽ rozwiÄ…zaĹ‚ ten quiz
    latest_attempt = QuizAttempt.objects.filter(
        user=request.user, 
        quiz=quiz,
        completed_at__isnull=False
    ).order_by('-completed_at').first()
    
    # JeĹ›li jest ukoĹ„czona prĂłba, przekieruj do wynikĂłw
    if latest_attempt:
        return redirect('training:quiz_result', pk=pk, attempt_id=latest_attempt.id)
    
    if request.method == 'POST':
        score = 0
        total = questions.count()
        
        # UtwĂłrz prĂłbÄ™
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=0,  # Zaktualizujemy pĂłĹşniej
            total_questions=total,
            percentage=0,  # Zaktualizujemy pĂłĹşniej
            completed_at=timezone.now(),
            passed=False  # Zaktualizujemy pĂłĹşniej
        )
        
        # Zapisz odpowiedzi uĹĽytkownika
        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            selected_answer = None
            is_correct = False
            
            if selected_answer_id:
                try:
                    selected_answer = QuizAnswer.objects.get(id=selected_answer_id)
                    is_correct = selected_answer.is_correct
                    if is_correct:
                        score += 1
                except QuizAnswer.DoesNotExist:
                    pass
            
            # Zapisz odpowiedĹş uĹĽytkownika
            UserQuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct
            )
        
        # Zaktualizuj wynik prĂłby
        percentage = (score / total * 100) if total > 0 else 0
        passed = percentage >= quiz.passing_score
        
        attempt.score = score
        attempt.percentage = percentage
        attempt.passed = passed
        attempt.save()
        
        # Aktualizuj licznik prĂłb
        quiz.attempts_count += 1
        quiz.save()
        
        messages.success(request, f'Quiz zakoĹ„czony! Wynik: {score}/{total} ({percentage:.0f}%)')
        return redirect('training:quiz_result', pk=pk, attempt_id=attempt.id)
    
    return render(request, 'training/quiz_take.html', {
        'quiz': quiz,
        'questions': questions,
    })

@login_required
def quiz_result(request, pk, attempt_id):
    """Wyniki quizu z szczegĂłĹ‚ami odpowiedzi"""
    quiz = get_object_or_404(Quiz, pk=pk)
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user, quiz=quiz)
    
    # Pobierz wszystkie prĂłby uĹĽytkownika dla tego quizu
    attempts = QuizAttempt.objects.filter(
        user=request.user, quiz=quiz
    ).order_by('-started_at')
    
    # Pobierz odpowiedzi uĹĽytkownika dla tej prĂłby
    user_answers = attempt.user_answers.select_related(
        'question', 'selected_answer'
    ).prefetch_related('question__answers').all()
    
    # Przygotuj dane pytaĹ„ z odpowiedziami
    questions_data = []
    for user_answer in user_answers:
        question = user_answer.question
        all_answers = question.answers.all()
        correct_answer = all_answers.filter(is_correct=True).first()
        
        questions_data.append({
            'question': question,
            'user_answer': user_answer.selected_answer,
            'correct_answer': correct_answer,
            'is_correct': user_answer.is_correct,
            'all_answers': all_answers
        })

    # Statystyki
    if attempts.exists():
        best_score = attempts.order_by('-percentage').first()
        avg_score = sum(a.percentage for a in attempts) / attempts.count()
    else:
        best_score = None
        avg_score = 0

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'questions_data': questions_data,
        'attempts': attempts,
        'best_score': best_score,
        'avg_score': avg_score,
    }
    return render(request, 'training/quiz_result.html', context)

@login_required
def my_results(request):
    """Lista wszystkich prób użytkownika (Moje wyniki)"""
    attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz').order_by('-started_at')

    return render(request, 'training/my_results.html', {
        'attempts': attempts,
    })

def index(request):
    """Widok index - przekierowanie na stronÄ™ gĹ‚ĂłwnÄ…"""
    from django.shortcuts import redirect
    return redirect('training:home')

# ===== ZAJÄCIA INDYWIDUALNE =====

@login_required
def private_lessons_list(request):
    """Lista dostÄ™pnych zajÄ™Ä‡ indywidualnych"""
    # Pobierz wszystkie dostÄ™pne terminy (nieuczÄ™szczane)
