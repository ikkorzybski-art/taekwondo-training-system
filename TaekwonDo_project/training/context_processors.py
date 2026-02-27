from django.db import models
from .models import QuizAttempt

def quiz_points(request):
    if request.user.is_authenticated:
        quiz_attempts = QuizAttempt.objects.filter(user=request.user)
        quiz_points = quiz_attempts.aggregate(total_points=models.Sum('score'))['total_points'] or 0
        return {'quiz_points': quiz_points}
    return {'quiz_points': 0}