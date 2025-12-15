from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    # Strona główna
    path('', views.home, name='home'),
    path('index/', views.index, name='index'),
    
    # Autoryzacja
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # Dashboard i profil
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Dni treningowe
    path('training-days/', views.training_days_list, name='training_days_list'),
    path('training-days/create/', views.training_day_create, name='training_day_create'),
    path('training-days/<int:pk>/edit/', views.training_day_edit, name='training_day_edit'),
    path('training-days/<int:pk>/delete/', views.training_day_delete, name='training_day_delete'),
    
    # Obecność
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/create/', views.attendance_create, name='attendance_create'),
    path('attendance/export/', views.attendance_export_csv, name='attendance_export_csv'),
    
    # Fiszki
    path('flashcards/', views.flashcards_list, name='flashcards_list'),
    path('flashcards/create/', views.flashcard_create, name='flashcard_create'),
    
    # Quizy
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/<int:pk>/take/', views.quiz_take, name='quiz_take'),
    path('quizzes/<int:pk>/result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    
    # Zajęcia indywidualne (ADMIN)
    path('manage-private-lessons/', views.manage_private_lessons, name='manage_private_lessons'),
    path('generate-weekly-lessons/', views.generate_weekly_lessons, name='generate_weekly_lessons'),
    path('private-lessons/delete/<int:lesson_id>/', views.delete_private_lesson, name='delete_private_lesson'),
    path('private-lessons/complete/<int:lesson_id>/', views.mark_lesson_completed, name='mark_lesson_completed'),
]