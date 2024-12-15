from answer.models import ExamAnswer, QuestionAnswer
from answer.serializers import AnswerExamSerializer
from django.db import IntegrityError
from django.test import TestCase
from exam.models import Exam, ExamQuestion
from question.models import Alternative, Question
from student.models import Student


class AnswerExamSerializerTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(name="João da Silva")

        self.exam = Exam.objects.create(name="Exame de Matemática")

        self.question1 = Question.objects.create(content="Questão 1")
        self.question2 = Question.objects.create(content="Questão 2")
        self.question3 = Question.objects.create(content="Questão 3")

        ExamQuestion.objects.create(exam=self.exam, question=self.question1, number=1)
        ExamQuestion.objects.create(exam=self.exam, question=self.question2, number=2)
        ExamQuestion.objects.create(exam=self.exam, question=self.question3, number=3)

        self.alt_q1_a = Alternative.objects.create(
            question=self.question1,
            content="Alternativa A da Q1",
            option=1,
            is_correct=False,
        )
        self.alt_q1_b = Alternative.objects.create(
            question=self.question1,
            content="Alternativa B da Q1 (correta)",
            option=2,
            is_correct=True,
        )
        self.alt_q2_a = Alternative.objects.create(
            question=self.question2,
            content="Alternativa A da Q2",
            option=1,
            is_correct=True,
        )
        self.alt_q3_a = Alternative.objects.create(
            question=self.question3,
            content="Alternativa A da Q3",
            option=1,
            is_correct=True,
        )

        self.base_data = {
            "student_id": self.student.id,
            "question_responses": [
                {
                    "question_id": self.question1.id,
                    "selected_alternative_id": self.alt_q1_a.id,
                },
                {
                    "question_id": self.question2.id,
                    "selected_alternative_id": self.alt_q2_a.id,
                },
                {
                    "question_id": self.question3.id,
                    "selected_alternative_id": self.alt_q3_a.id,
                },
            ],
        }

    def test_successful_validation_and_creation(self):
        """Testa se o serializer valida corretamente e cria um ExamAnswer sem erros."""
        serializer = AnswerExamSerializer(
            data=self.base_data, context={"exam": self.exam}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        exam_answer = serializer.save()
        self.assertIsInstance(exam_answer, ExamAnswer)
        self.assertEqual(exam_answer.exam, self.exam)
        self.assertEqual(exam_answer.student, self.student)
        self.assertEqual(
            QuestionAnswer.objects.filter(exam_response=exam_answer).count(), 3
        )

    def test_repeated_questions_not_allowed(self):
        """Testa se o serializer rejeita respostas duplicadas para a mesma questão."""
        data = self.base_data.copy()
        # Duplica a question1
        data["question_responses"].append(
            {
                "question_id": self.question1.id,
                "selected_alternative_id": self.alt_q1_b.id,
            }
        )

        serializer = AnswerExamSerializer(data=data, context={"exam": self.exam})
        self.assertFalse(serializer.is_valid())
        # Esperamos mensagem de erro sobre questões repetidas
        self.assertIn("Repeated questions are not allowed", str(serializer.errors))

    def test_must_answer_all_questions(self):
        """
        Testa se o serializer rejeita quando nem todas as questões do exame são respondidas
        (exemplo: responder só 2 de um total de 3).
        """
        data = self.base_data.copy()

        # Remove a última questão para simular "faltando resposta"
        data["question_responses"].pop()

        serializer = AnswerExamSerializer(data=data, context={"exam": self.exam})
        self.assertFalse(serializer.is_valid())
        self.assertIn("All exam's questions must be answered", str(serializer.errors))

    def test_questions_must_be_from_exam(self):
        """
        Testa se o serializer rejeita questões que não fazem parte do exame.
        """
        # Cria uma questão que não pertence ao exame
        question_outside = Question.objects.create(content="Questão Fora do Exame")

        data = self.base_data.copy()

        # Substitui a question3 por uma questão que não está associada ao exame
        data["question_responses"][2]["question_id"] = question_outside.id

        serializer = AnswerExamSerializer(data=data, context={"exam": self.exam})
        self.assertFalse(serializer.is_valid())
        self.assertIn("All questions must be from the exam", str(serializer.errors))

    def test_student_cannot_answer_twice(self):
        """Testa se o serializer rejeita submissão duplicada do mesmo estudante para o mesmo exame."""
        # Cria previamente um ExamAnswer para simular que o estudante já respondeu
        _ = ExamAnswer.objects.create(exam=self.exam, student=self.student)

        serializer = AnswerExamSerializer(
            data=self.base_data, context={"exam": self.exam}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("Student already answered this exam", str(serializer.errors))

    def test_exam_answer_creation_is_atomic(self):
        """
        Testa se a criação do ExamAnswer e QuestionAnswer ocorre de forma atômica.
        Simulamos um erro forçado no meio do processo para garantir que tudo é revertido.
        """
        original_create_questionanswer = QuestionAnswer.objects.create

        def mock_create_questionanswer(*args, **kwargs):
            # Dispara erro no meio da criação das respostas, forçando rollback
            selected_alternative = kwargs.get("selected_alternative")
            # Vamos supor que se a ID for a mesma que alt_q2_a, damos erro proposital
            if selected_alternative == self.alt_q2_a:
                raise IntegrityError("Erro simulado durante criação de QuestionAnswer")
            return original_create_questionanswer(*args, **kwargs)

        try:
            QuestionAnswer.objects.create = mock_create_questionanswer

            serializer = AnswerExamSerializer(
                data=self.base_data, context={"exam": self.exam}
            )
            self.assertTrue(serializer.is_valid(), serializer.errors)

            # Esperamos que ao salvar, dispare IntegrityError e reverta tudo
            with self.assertRaises(IntegrityError):
                serializer.save()

            # Verifica se nada foi criado
            self.assertEqual(ExamAnswer.objects.count(), 0)
            self.assertEqual(QuestionAnswer.objects.count(), 0)

        finally:
            # Restaura método original
            QuestionAnswer.objects.create = original_create_questionanswer
