import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, TrainingDay, Attendance, Flashcard, Quiz
import secrets
import string

def generate_random_password(length=12):
    """Generuje losowe, bezpieczne hasło"""
    # Znaki: małe litery, duże litery, cyfry, znaki specjalne
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    # Upewnij się, że hasło zawiera wszystkie typy znaków
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*"),
    ]
    # Dodaj pozostałe losowe znaki
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Przetasuj znaki
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

class CustomUserCreationForm(UserCreationForm):
    """Formularz rejestracji"""
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'twoj@email.com'})
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label='Imię',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jan'})
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        label='Nazwisko',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kowalski'})
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label='Telefon',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+48 123 456 789'})
    )
    date_of_birth = forms.DateField(
        required=False,
        label='Data urodzenia',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    generate_password = forms.BooleanField(
        required=False,
        initial=True,
        label='Wygeneruj losowe hasło',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'generate_password_checkbox'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Powtórz hasło'
        })
        
        # Polskie etykiety
        self.fields['username'].label = 'Nazwa użytkownika'
        self.fields['password1'].label = 'Hasło'
        self.fields['password2'].label = 'Potwierdź hasło'
        self.fields['password1'].help_text = 'Minimum 8 znaków'
        self.fields['username'].help_text = ''
        self.fields['password2'].help_text = ''
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ten adres email jest już zajęty.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Aktualizuj profil
            profile = user.profile
            if self.cleaned_data.get('phone'):
                profile.phone = self.cleaned_data['phone']
            if self.cleaned_data.get('date_of_birth'):
                profile.date_of_birth = self.cleaned_data['date_of_birth']
            profile.save()
        
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """Formularz logowania"""
    username = forms.CharField(
        label='Nazwa użytkownika',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Hasło',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
    )

class UserProfileForm(forms.ModelForm):
    """Formularz profilu"""
    class Meta:
        model = UserProfile
        fields = ['belt_level', 'phone', 'date_of_birth', 'address', 'emergency_contact']
        widgets = {
            'belt_level': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TrainingDayForm(forms.ModelForm):
    """Formularz dni treningowych"""
    class Meta:
        model = TrainingDay
        fields = ['weekday', 'start_time', 'end_time', 'location', 'instructor', 
                  'max_participants', 'is_active', 'description']
        widgets = {
            'weekday': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AttendanceForm(forms.ModelForm):
    """Formularz obecności"""
    class Meta:
        model = Attendance
        fields = ['user', 'training_day', 'date', 'present', 'notes']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'training_day': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'present': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class FlashcardForm(forms.ModelForm):
    """Formularz fiszek"""
    class Meta:
        model = Flashcard
        fields = ['category', 'question', 'answer', 'group', 'is_public']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'question': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ChangePasswordForm(forms.Form):
    """Formularz zmiany hasła"""
    old_password = forms.CharField(
        label='Stare hasło',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Stare hasło'})
    )
    new_password1 = forms.CharField(
        label='Nowe hasło',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nowe hasło'})
    )
    new_password2 = forms.CharField(
        label='Powtórz nowe hasło',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Powtórz nowe hasło'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Stare hasło jest nieprawidłowe.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError('Nowe hasła nie są zgodne.')
        return cleaned_data

    def save(self, commit=True):
        new_password = self.cleaned_data['new_password1']
        self.user.set_password(new_password)
        if commit:
            self.user.save()
        return self.user