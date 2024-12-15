from django.test import TestCase

from exam.models import Exam
from student.models import Student

# Create your tests here.

class AnswerExamTestCase(TestCase):
    def setUp(self):
        
        Exam.objects.create(name='Exam 1')
        Student.objects.create(name='Student 1')
        return super().setUp()