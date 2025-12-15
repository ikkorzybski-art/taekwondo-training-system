from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    # Strona główna
    path('', views.home, name='home'),
    path('index/', views.index, name='index'),
    
    # Autoryzacja
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # Dashboard i profil
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Dni treningowe
    path('training-days/', views.training_days_list, name='training_days_list'),
    
    # Obecność
    path('attendance/', views.attendance_list, name='attendance_list'),
    
    # Fiszki
    path('flashcards/', views.flashcards_list, name='flashcards_list'),
    path('flashcards/create/', views.flashcard_create, name='flashcard_create'),
    
    # Quizy
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/<int:pk>/take/', views.quiz_take, name='quiz_take'),
    path('quizzes/<int:pk>/result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('my-quiz-results/', views.my_quiz_results, name='my_quiz_results'),
    
    # Zajęcia indywidualne
    path('private-lessons/', views.private_lessons_list, name='private_lessons'),
    path('private-lessons/book/<int:lesson_id>/', views.book_private_lesson, name='book_private_lesson'),
    path('my-private-lessons/', views.my_private_lessons, name='my_private_lessons'),
    path('private-lessons/cancel/<int:lesson_id>/', views.cancel_private_lesson, name='cancel_private_lesson'),
    
    # Egzaminy
    path('exams/', views.exam_list, name='exam_list'),
]