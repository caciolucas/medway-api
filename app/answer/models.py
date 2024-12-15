from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class ExamAnswer(models.Model):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EVALUATED = "EVALUETED"
    STATUS_CHOICES = [
        (PENDING, _("Pending")),
        (PROCESSING, _("Processing")),
        (EVALUATED, _("Evaluated")),
    ]
    student = models.ForeignKey(
        "student.Student", on_delete=models.CASCADE, related_name="responses"
    )
    exam = models.ForeignKey(
        "exam.Exam", on_delete=models.CASCADE, related_name="responses"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    # NOTE: Could add the results here, in a separated model or leave it to the serializer and cache it.
    # Going for the last option.

    class Meta:
        unique_together = ("student", "exam")
        indexes = [models.Index(fields=["student", "exam"])]

    def __str__(self):
        return f"{self.student} - {self.exam}"


class QuestionAnswer(models.Model):
    exam_response = models.ForeignKey(
        ExamAnswer, on_delete=models.CASCADE, related_name="question_responses"
    )
    question = models.ForeignKey("question.Question", on_delete=models.CASCADE)
    selected_alternative = models.ForeignKey(
        "question.Alternative", on_delete=models.CASCADE, null=True, blank=True
    )
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ("exam_response", "question")
        indexes = [models.Index(fields=["exam_response", "question"])]

    def __str__(self):
        return f"{self.exam_response} - {self.question}"
