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
                     Quiz, QuizQuestion, QuizAnswer, QuizAttempt, PrivateLesson, Exam, UserQuizAnswer)
from .forms import (CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, 
                    TrainingDayForm, AttendanceForm, FlashcardForm)

# ===== LOGOWANIE =====

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

# ===== OBECNOŚĆ =====

@login_required
def attendance_list(request):
    """Lista obecności - tylko własna"""
    attendances = Attendance.objects.filter(user=request.user).select_related('training_day')
    
    # Filtrowanie
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        attendances = attendances.filter(date__gte=date_from)
    if date_to:
        attendances = attendances.filter(date__lte=date_to)
    
    # Statystyki
    total_present = attendances.filter(present=True).count()
    total_absent = attendances.filter(present=False).count()
    
    context = {
        'attendances': attendances[:50],  # Limit 50 wyników
        'total_present': total_present,
        'total_absent': total_absent,
    }
    return render(request, 'training/attendance_list.html', context)

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
    
    # Jeśli jest ukończona próba, przekieruj do wyników
    if latest_attempt:
        return redirect('training:quiz_result', pk=pk, attempt_id=latest_attempt.id)
    
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

@login_required
def my_quiz_results(request):
    """Widok wszystkich wyników użytkownika z quizów"""
    # Pobierz wszystkie próby użytkownika
    all_attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz').order_by('-started_at')
    
    # Grupuj próby po quizach
    from collections import defaultdict
    quizzes_data = defaultdict(list)
    
    for attempt in all_attempts:
        quizzes_data[attempt.quiz].append(attempt)
    
    # Przygotuj statystyki dla każdego quizu
    quiz_stats = []
    for quiz, attempts in quizzes_data.items():
        best_attempt = max(attempts, key=lambda x: x.percentage)
        latest_attempt = attempts[0]  # już posortowane po started_at desc
        avg_percentage = sum(a.percentage for a in attempts) / len(attempts)
        passed_count = sum(1 for a in attempts if a.passed)
        
        quiz_stats.append({
            'quiz': quiz,
            'attempts_count': len(attempts),
            'best_attempt': best_attempt,
            'latest_attempt': latest_attempt,
            'avg_percentage': avg_percentage,
            'passed_count': passed_count,
            'all_attempts': attempts[:5]  # Ostatnie 5 prób
        })
    
    # Sortuj quizy po dacie ostatniej próby
    quiz_stats.sort(key=lambda x: x['latest_attempt'].started_at, reverse=True)
    
    # Ogólne statystyki
    total_attempts = all_attempts.count()
    total_passed = all_attempts.filter(passed=True).count()
    total_quizzes = len(quizzes_data)
    
    if total_attempts > 0:
        overall_avg = sum(a.percentage for a in all_attempts) / total_attempts
        pass_rate = (total_passed / total_attempts * 100) if total_attempts > 0 else 0
    else:
        overall_avg = 0
        pass_rate = 0
    
    context = {
        'quiz_stats': quiz_stats,
        'total_attempts': total_attempts,
        'total_passed': total_passed,
        'total_quizzes': total_quizzes,
        'overall_avg': overall_avg,
        'pass_rate': pass_rate,
    }
    return render(request, 'training/my_quiz_results.html', context)

def index(request):
    """Widok index - przekierowanie na stronę główną"""
    from django.shortcuts import redirect
    return redirect('training:home')

# ===== ZAJĘCIA INDYWIDUALNE =====

@login_required
def private_lessons_list(request):
    """Lista dostępnych zajęć indywidualnych"""
    # Pobierz wszystkie dostępne terminy (nieuczęszczane)
    available_lessons = PrivateLesson.objects.filter(
        status='available'
    ).select_related('instructor').order_by('date', 'start_time')
    
    # Grupuj po instruktorach
    from collections import defaultdict
    lessons_by_instructor = defaultdict(list)
    for lesson in available_lessons:
        lessons_by_instructor[lesson.instructor].append(lesson)
    
    context = {
        'lessons_by_instructor': dict(lessons_by_instructor),
        'available_lessons': available_lessons,
    }
    return render(request, 'training/private_lessons.html', context)

@login_required
@require_http_methods(["POST"])
def book_private_lesson(request, lesson_id):
    """Zapisz się na zajęcia indywidualne"""
    lesson = get_object_or_404(PrivateLesson, id=lesson_id, status='available')
    
    # Sprawdź limit 5 osób na dany dzień
    booked_on_date = PrivateLesson.objects.filter(
        date=lesson.date,
        status='booked'
    ).count()
    
    if booked_on_date >= 5:
        messages.error(request, 'Osiągnięto maksymalną ilość osób na ten dzień. Wybierz inny termin.')
        return redirect('training:private_lessons')
    
    # Sprawdź czy użytkownik nie ma już zarezerwowanych zajęć w tym samym czasie
    conflicting = PrivateLesson.objects.filter(
        student=request.user,
        date=lesson.date,
        status__in=['booked', 'completed']
    ).filter(
        Q(start_time__lt=lesson.end_time, end_time__gt=lesson.start_time)
    ).exists()
    
    if conflicting:
        messages.error(request, 'Masz już zarezerwowane zajęcia w tym czasie!')
        return redirect('training:private_lessons')
    
    # Zarezerwuj zajęcia
    lesson.student = request.user
    lesson.status = 'booked'
    lesson.save()
    
    messages.success(request, f'Zapisano na zajęcia z {lesson.instructor.get_full_name()} w dniu {lesson.date} o {lesson.start_time}')
    return redirect('training:my_private_lessons')

@login_required
def my_private_lessons(request):
    """Moje zarezerwowane zajęcia indywidualne"""
    my_lessons = PrivateLesson.objects.filter(
        student=request.user
    ).select_related('instructor').order_by('-date', '-start_time')
    
    # Podziel na nadchodzące i przeszłe
    today = timezone.now().date()
    upcoming = my_lessons.filter(date__gte=today, status__in=['booked'])
    past = my_lessons.filter(Q(date__lt=today) | Q(status__in=['completed', 'cancelled']))
    
    context = {
        'upcoming_lessons': upcoming,
        'past_lessons': past,
    }
    return render(request, 'training/my_private_lessons.html', context)

@login_required
@require_http_methods(["POST"])
def cancel_private_lesson(request, lesson_id):
    """Anuluj zarezerwowane zajęcia"""
    lesson = get_object_or_404(PrivateLesson, id=lesson_id, student=request.user)
    
    if lesson.status != 'booked':
        messages.error(request, 'Nie można anulować tych zajęć!')
        return redirect('training:my_private_lessons')
    
    # Sprawdź czy nie za późno (minimum 24h przed zajęciami)
    lesson_datetime = timezone.make_aware(
        datetime.combine(lesson.date, lesson.start_time)
    )
    if timezone.now() + timedelta(hours=24) > lesson_datetime:
        messages.error(request, 'Nie można anulować zajęć na mniej niż 24 godziny przed rozpoczęciem!')
        return redirect('training:my_private_lessons')
    
    # Anuluj
    lesson.student = None
    lesson.status = 'available'
    lesson.save()
    
    messages.success(request, 'Zajęcia zostały anulowane.')
    return redirect('training:my_private_lessons')

# ===== EGZAMINY =====

@login_required
def exam_list(request):
    """Lista nadchodzących egzaminów"""
    today = timezone.now().date()
    upcoming_exams = Exam.objects.filter(date__gte=today).order_by('date', 'time')
    past_exams = Exam.objects.filter(date__lt=today).order_by('-date', '-time')[:5]  # 5 ostatnich
    
    context = {
        'upcoming_exams': upcoming_exams,
        'past_exams': past_exams,
    }
    return render(request, 'training/exam_list.html', context)