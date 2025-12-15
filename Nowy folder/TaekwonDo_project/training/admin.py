from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
import re
from .models import (UserProfile, TrainingDay, Attendance, Flashcard, 
                     Quiz, QuizQuestion, QuizAnswer, QuizAttempt, UserQuizAnswer)
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import csv
from datetime import datetime, timedelta

from .models import (UserProfile, TrainingDay, Attendance, Flashcard, 
                     Quiz, QuizQuestion, QuizAnswer, QuizAttempt)
from .forms import (CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, 
                    TrainingDayForm, AttendanceForm, FlashcardForm)

# Inline admin dla profilu
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Profil'
    verbose_name_plural = 'Profile'
    fields = ['belt_level', 'phone', 'date_of_birth', 'address', 'emergency_contact']
    min_num = 1
    max_num = 1
    extra = 0

# Niestandardowy formularz dodawania użytkownika
class CustomUserCreationAdminForm(forms.ModelForm):
    """Formularz tworzenia użytkownika bez pola hasła"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 
                  'is_superuser', 'groups', 'user_permissions')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('To pole jest wymagane.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Użytkownik o tej nazwie już istnieje.')
        return username

# Formularz edycji użytkownika z możliwością podglądu/zmiany hasła
class CustomUserChangeAdminForm(forms.ModelForm):
    """Formularz edycji użytkownika z opcją wyświetlania/zmiany hasła"""
    temporary_password = forms.CharField(
        label='Hasło tymczasowe (tylko do odczytu)',
        required=False,
        disabled=True,
        help_text='Hasło przypisane użytkownikowi przy tworzeniu konta',
        widget=forms.TextInput(attrs={'class': 'vTextField', 'readonly': 'readonly'})
    )
    new_password = forms.CharField(
        label='Nowe hasło (opcjonalnie)',
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Wypełnij tylko jeśli chcesz zmienić hasło użytkownika'
    )
    
    class Meta:
        model = User
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and hasattr(self.instance, 'profile'):
            # Wypełnij pole hasła tymczasowego
            self.fields['temporary_password'].initial = self.instance.profile.temporary_password or '(brak)'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Jeśli wprowadzono nowe hasło, ustaw je
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])
            # Zaktualizuj hasło tymczasowe w profilu
            if hasattr(user, 'profile'):
                user.profile.temporary_password = self.cleaned_data['new_password']
                user.profile.must_change_password = True
                if commit:
                    user.profile.save()
        if commit:
            user.save()
        return user

# Rozszerzony User Admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_belt', 
                    'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    # Użyj niestandardowych formularzy
    add_form = CustomUserCreationAdminForm
    form = CustomUserChangeAdminForm
    
    # Modyfikacja formularza dodawania użytkownika
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name'),
        }),
        ('Uprawnienia', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    
    # Modyfikacja formularza edycji użytkownika
    fieldsets = (
        (None, {'fields': ('username', 'temporary_password', 'new_password')}),
        ('Informacje osobiste', {'fields': ('first_name', 'last_name', 'email')}),
        ('Uprawnienia', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Daty ważne', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Tylko dla nowych użytkowników
            # Generuj losowe hasło
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            temporary_password = ''.join(secrets.choice(alphabet) for i in range(12))
            obj.set_password(temporary_password)
            # Zapisz użytkownika
            super().save_model(request, obj, form, change)
            # Poczekaj na utworzenie profilu przez inline lub sygnał
            from django.db import transaction
            transaction.on_commit(lambda: self._save_temp_password(obj, temporary_password))
        else:
            super().save_model(request, obj, form, change)
    
    def _save_temp_password(self, user, password):
        """Zapisz hasło tymczasowe w profilu po zacommitowaniu transakcji"""
        try:
            if hasattr(user, 'profile'):
                user.profile.temporary_password = password
                user.profile.must_change_password = True
                user.profile.save()
        except Exception as e:
            # Loguj błąd ale nie przerywaj procesu
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Nie można zapisać hasła tymczasowego dla użytkownika {user.username}: {str(e)}')
    
    def get_belt(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_belt_level_display()
        return '-'
    get_belt.short_description = 'Pas'

# Przerejstrowanie User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'belt_level', 'phone', 'temporary_password', 'must_change_password', 'created_at']
    list_filter = ['belt_level', 'must_change_password', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Użytkownik', {
            'fields': ('user',)
        }),
        ('Informacje podstawowe', {
            'fields': ('belt_level', 'phone', 'date_of_birth')
        }),
        ('Hasło', {
            'fields': ('temporary_password', 'must_change_password'),
            'description': 'Hasło tymczasowe przypisane użytkownikowi przy tworzeniu konta'
        }),
        ('Dodatkowe informacje', {
            'fields': ('address', 'emergency_contact')
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# TrainingDay Admin
@admin.register(TrainingDay)
class TrainingDayAdmin(admin.ModelAdmin):
    list_display = ['get_weekday', 'start_time', 'end_time', 'location', 
                    'instructor', 'max_participants', 'is_active']
    list_filter = ['weekday', 'is_active', 'instructor']
    search_fields = ['location', 'description']
    list_editable = ['is_active']
    
    def get_weekday(self, obj):
        return obj.get_weekday_display()
    get_weekday.short_description = 'Dzień tygodnia'
    get_weekday.admin_order_field = 'weekday'
    
    fieldsets = (
        ('Termin', {
            'fields': ('weekday', 'start_time', 'end_time')
        }),
        ('Szczegóły', {
            'fields': ('location', 'instructor', 'max_participants', 'is_active')
        }),
        ('Opis', {
            'fields': ('description',)
        }),
    )

# Attendance Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'training_day', 'date', 'get_status', 'created_by']
    list_filter = ['present', 'date', 'training_day']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'created_by']
    
    def get_status(self, obj):
        if obj.present:
            return format_html('<span style="color: green;">✓ Obecny</span>')
        return format_html('<span style="color: red;">✗ Nieobecny</span>')
    get_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('user', 'training_day', 'date', 'present')
        }),
        ('Dodatkowe', {
            'fields': ('notes', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_present', 'mark_as_absent']
    
    def mark_as_present(self, request, queryset):
        updated = queryset.update(present=True)
        self.message_user(request, f'{updated} rekordów oznaczono jako obecne.')
    mark_as_present.short_description = 'Oznacz jako obecne'
    
    def mark_as_absent(self, request, queryset):
        updated = queryset.update(present=False)
        self.message_user(request, f'{updated} rekordów oznaczono jako nieobecne.')
    mark_as_absent.short_description = 'Oznacz jako nieobecne'

# Flashcard Admin
@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['get_question_preview', 'category', 'group', 'is_public', 
                    'views_count', 'created_by']
    list_filter = ['category', 'group', 'is_public', 'created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'views_count']
    list_editable = ['is_public']
    
    def get_question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    get_question_preview.short_description = 'Pytanie'
    
    fieldsets = (
        ('Treść', {
            'fields': ('category', 'question', 'answer', 'group')
        }),
        ('Ustawienia', {
            'fields': ('is_public', 'created_by')
        }),
        ('Statystyki', {
            'fields': ('views_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )

# QuizAnswer Inline
class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 4
    fields = ['answer_text', 'is_correct']

# QuizQuestion Inline
class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'text_answer', 'order', 'points']
    show_change_link = True

# Quiz Admin
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'get_questions_count', 'time_limit', 
                    'passing_score', 'attempts_count', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['attempts_count', 'created_at']
    list_editable = ['is_active']
    inlines = [QuizQuestionInline]
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    get_questions_count.short_description = 'Liczba pytań'
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('title', 'description', 'category')
        }),
        ('Ustawienia quizu', {
            'fields': ('time_limit', 'passing_score', 'is_active')
        }),
        ('Autor i statystyki', {
            'fields': ('created_by', 'attempts_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )

# QuizQuestion Admin
@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'get_question_preview', 'order', 'points']
    list_filter = ['quiz']
    search_fields = ['question_text']
    inlines = [QuizAnswerInline]
    
    def get_question_preview(self, obj):
        return obj.question_text[:60] + '...' if len(obj.question_text) > 60 else obj.question_text
    get_question_preview.short_description = 'Pytanie'

# QuizAnswer Admin
@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'get_answer_preview', 'is_correct']
    list_filter = ['is_correct', 'question__quiz']
    search_fields = ['answer_text']
    
    def get_answer_preview(self, obj):
        text = obj.answer_text[:50] + '...' if len(obj.answer_text) > 50 else obj.answer_text
        if obj.is_correct:
            return format_html('<span style="color: green; font-weight: bold;">✓ {}</span>', text)
        return text
    get_answer_preview.short_description = 'Odpowiedź'

# QuizAttempt Admin
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'total_questions', 'get_percentage', 
                    'get_status', 'started_at']
    list_filter = ['passed', 'started_at', 'quiz']
    search_fields = ['user__username', 'quiz__title']
    date_hierarchy = 'started_at'
    readonly_fields = ['started_at', 'completed_at']
    
    def get_percentage(self, obj):
        return f"{obj.percentage:.1f}%"
    get_percentage.short_description = 'Wynik %'
    
    def get_status(self, obj):
        if obj.passed:
            return format_html('<span style="color: green; font-weight: bold;">✓ Zaliczony</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Niezaliczony</span>')
    get_status.short_description = 'Status'
    
    fieldsets = (
        ('Próba quizu', {
            'fields': ('user', 'quiz')
        }),
        ('Wynik', {
            'fields': ('score', 'total_questions', 'percentage', 'passed')
        }),
        ('Czas', {
            'fields': ('started_at', 'completed_at')
        }),
    )


# UserQuizAnswer Admin
@admin.register(UserQuizAnswer)
class UserQuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_quiz', 'question_preview', 'selected_answer', 'is_correct']
    list_filter = ['is_correct', 'attempt__quiz', 'attempt__user']
    search_fields = ['question__text', 'attempt__user__username']
    readonly_fields = ['attempt', 'question', 'selected_answer', 'is_correct']
    
    def get_user(self, obj):
        return obj.attempt.user.username
    get_user.short_description = 'Użytkownik'
    
    def get_quiz(self, obj):
        return obj.attempt.quiz.title
    get_quiz.short_description = 'Quiz'
    
    def question_preview(self, obj):
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text
    question_preview.short_description = 'Pytanie'
    
    def has_add_permission(self, request):
        return False  # Nie pozwalaj ręcznie dodawać odpowiedzi
    
    def has_change_permission(self, request, obj=None):
        return False  # Nie pozwalaj edytować odpowiedzi


# Dostosowanie panelu admina
admin.site.site_header = 'Panel Administracyjny Taekwon-Do'
admin.site.site_title = 'Admin Taekwon-Do'
admin.site.index_title = 'Zarządzanie systemem treningowym'