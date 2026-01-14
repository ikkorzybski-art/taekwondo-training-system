from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt
from django.utils import timezone

class QuizRetryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        # Create quiz and question/answer
        self.quiz = Quiz.objects.create(title='Test Quiz', is_active=True, passing_score=50)
        q = QuizQuestion.objects.create(quiz=self.quiz, text='Q1')
        a1 = QuizAnswer.objects.create(question=q, text='A1', is_correct=True)
        a2 = QuizAnswer.objects.create(question=q, text='A2', is_correct=False)
        # Create a completed attempt so default behavior would redirect
        self.attempt = QuizAttempt.objects.create(
            user=self.user,
            quiz=self.quiz,
            score=1,
            total_questions=1,
            percentage=100,
            completed_at=timezone.now(),
            passed=True
        )

    def test_retry_allows_access_to_quiz_take(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('training:quiz_take', kwargs={'pk': self.quiz.pk}) + '?retry=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'training/quiz_take.html')

    def test_without_retry_redirects_to_result(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('training:quiz_take', kwargs={'pk': self.quiz.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('training:quiz_result', kwargs={'pk': self.quiz.pk, 'attempt_id': self.attempt.id}), response['Location'])
