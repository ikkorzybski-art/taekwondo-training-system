from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, Flashcard
from django.utils import timezone

class QuizRetryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        # Create quiz and question/answer
        self.quiz = Quiz.objects.create(title='Test Quiz', description='desc', category='techniques', is_active=True, passing_score=50, max_group='white')
        q = QuizQuestion.objects.create(quiz=self.quiz, question_text='Q1')
        a1 = QuizAnswer.objects.create(question=q, answer_text='A1', is_correct=True)
        a2 = QuizAnswer.objects.create(question=q, answer_text='A2', is_correct=False)
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


class GroupRestrictionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='greenuser', password='pass')
        # set profile to green
        self.user.profile.belt_level = 'green'
        self.user.profile.save()

        # create flashcards
        self.fc_green = Flashcard.objects.create(category='techniques', question='Q G', answer='A', group='green', is_public=True)
        self.fc_blue = Flashcard.objects.create(category='techniques', question='Q B', answer='A', group='blue', is_public=True)

        # create quizzes
        self.quiz_green = Quiz.objects.create(title='Quiz Green', description='g', category='techniques', is_active=True, passing_score=50, max_group='green')
        self.quiz_blue = Quiz.objects.create(title='Quiz Blue', description='b', category='techniques', is_active=True, passing_score=50, max_group='blue')

    def test_flashcards_filtered_by_belt(self):
        self.client.login(username='greenuser', password='pass')
        url = reverse('training:flashcards_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        flashcards = response.context['flashcards']
        self.assertIn(self.fc_green, flashcards)
        self.assertNotIn(self.fc_blue, flashcards)

    def test_quiz_take_restricted_for_higher_group(self):
        self.client.login(username='greenuser', password='pass')
        # Allowed quiz
        url_green = reverse('training:quiz_take', kwargs={'pk': self.quiz_green.pk})
        resp = self.client.get(url_green)
        self.assertEqual(resp.status_code, 200)

        # Restricted quiz
        url_blue = reverse('training:quiz_take', kwargs={'pk': self.quiz_blue.pk})
        resp2 = self.client.get(url_blue)
        # Should redirect to quiz list with error
        self.assertEqual(resp2.status_code, 302)
        self.assertIn(reverse('training:quiz_list'), resp2['Location'])
