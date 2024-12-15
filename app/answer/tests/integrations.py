from answer.models import ExamAnswer, QuestionAnswer
from django.urls import reverse
from exam.models import Exam, ExamQuestion
from medway_api.celery import app
from question.models import Alternative, Question
from rest_framework import status
from rest_framework.test import APITestCase
from student.models import Student


class ExamAnswerIntegrationTest(APITestCase):
    def setUp(self):
        app.conf.task_always_eager = True
        app.conf.task_eager_propagates = True

        self.student = Student.objects.create(name="Estudante 1")
        self.exam = Exam.objects.create(name="Exame de Integração")

        # Cria três questões e relaciona ao exame (via tabela intermediária)
        self.question1 = Question.objects.create(content="Questão 1")
        self.question2 = Question.objects.create(content="Questão 2")
        self.question3 = Question.objects.create(content="Questão 3")

        ExamQuestion.objects.create(exam=self.exam, question=self.question1, number=1)
        ExamQuestion.objects.create(exam=self.exam, question=self.question2, number=2)
        ExamQuestion.objects.create(exam=self.exam, question=self.question3, number=3)

        self.alt_q1_a = Alternative.objects.create(
            question=self.question1,
            content="Alternativa A1",
            option=1,
            is_correct=False,
        )
        self.alt_q1_b = Alternative.objects.create(
            question=self.question1,
            content="Alternativa B1 (correta)",
            option=2,
            is_correct=True,
        )
        self.alt_q2_a = Alternative.objects.create(
            question=self.question2,
            content="Alternativa A2 (correta)",
            option=1,
            is_correct=True,
        )
        self.alt_q2_b = Alternative.objects.create(
            question=self.question2,
            content="Alternativa B2",
            option=2,
            is_correct=False,
        )
        self.alt_q3_a = Alternative.objects.create(
            question=self.question3,
            content="Alternativa A3 (correta)",
            option=1,
            is_correct=True,
        )

        self.answer_payload = {
            "student_id": self.student.id,
            "question_responses": [
                {
                    "question_id": self.question1.id,
                    "selected_alternative_id": self.alt_q1_b.id,  # Q1 correta
                },
                {
                    "question_id": self.question2.id,
                    "selected_alternative_id": self.alt_q2_a.id,  # Q2 correta
                },
                {
                    "question_id": self.question3.id,
                    "selected_alternative_id": self.alt_q3_a.id,  # Q3 correta
                },
            ],
        }

    def tearDown(self):
        app.conf.task_always_eager = False
        app.conf.task_eager_propagates = False
        return super().tearDown()

    def test_exam_answer_integration_flow(self):
        """
        Testa o fluxo de integração completo:
        1) Faz POST no endpoint /exams/<exam_id>/answer
        2) Verifica se ExamAnswer e QuestionAnswer foram criados
        3) Verifica se evaluate_exam rodou (sincronamente, pois CELERY_TASK_ALWAYS_EAGER = True)
        4) Checa se o status final é EVALUATED e se as respostas estão marcadas como is_correct adequadamente
        """

        url = reverse("exam-answer", kwargs={"pk": self.exam.id})
        response = self.client.post(url, data=self.answer_payload, format="json")

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.content
        )
        self.assertIn("message", response.data)
        self.assertIn("id", response.data)

        exam_answer_id = response.data["id"]
        exam_answer = ExamAnswer.objects.get(id=exam_answer_id)
        exam_answer.refresh_from_db()

        self.assertEqual(exam_answer.exam, self.exam)
        self.assertEqual(exam_answer.student, self.student)
        self.assertEqual(exam_answer.status, ExamAnswer.EVALUATED)

        question_answers = QuestionAnswer.objects.filter(exam_response=exam_answer)
        self.assertEqual(question_answers.count(), 3)

        for qa in question_answers:
            self.assertTrue(qa.is_correct)
