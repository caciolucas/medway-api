import logging

from answer.models import ExamAnswer, QuestionAnswer
from answer.tasks import evaluate_exam
from django.db import transaction
from question.models import Alternative, Question
from question.serializers import AlternativeResultSerializer, QuestionSerializer
from rest_framework import serializers
from student.models import Student

logger = logging.getLogger("django")

# NOTE: Could also use a ModelSerializer but I'll use a Serializer to have more control over the fields.


class AnswerQuestionSerializer(serializers.Serializer):
    question_id = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_alternative_id = serializers.PrimaryKeyRelatedField(
        queryset=Alternative.objects.all()
    )


class AnswerExamSerializer(serializers.Serializer):
    student_id = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    question_responses = AnswerQuestionSerializer(many=True)

    def validate_question_responses(self, value):
        exam = self.context["exam"]
        answered_question_ids = [answer["question_id"].id for answer in value]
        errors = []
        if len(set(answered_question_ids)) != len(answered_question_ids):
            errors.append("Repeated questions are not allowed")

        if len(answered_question_ids) != Question.objects.filter(exams=exam).count():
            errors.append("All exam's questions must be answered")

        if not set(answered_question_ids).issubset(
            set(Question.objects.filter(exams=exam).values_list("id", flat=True))
        ):
            errors.append("All questions must be from the exam")

        if errors:
            raise serializers.ValidationError(errors)

        return value

    def validate(self, attrs):
        exam = self.context["exam"]
        student = attrs["student_id"]

        if ExamAnswer.objects.filter(exam=exam, student=student).exists():
            raise serializers.ValidationError(
                {"student_id": "Student already answered this exam"}
            )

        return super().validate(attrs)

    def create(self, validated_data):
        with transaction.atomic():
            question_responses = validated_data.pop("question_responses")
            validated_data["student"] = validated_data.pop("student_id")

            exam_response = ExamAnswer.objects.create(
                exam=self.context["exam"], **validated_data
            )

            for question_response in question_responses:
                question_response["selected_alternative"] = question_response.pop(
                    "selected_alternative_id"
                )
                question_response["question"] = question_response.pop("question_id")
                QuestionAnswer.objects.create(
                    exam_response=exam_response, **question_response
                )

        evaluate_exam.apply_async(
            args=(exam_response.id,),
            retry=True,
            retry_policy={
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 0.2,
                "interval_max": 0.5,
            },
        )

        return exam_response


class QuestionAnswerResultSerializer(serializers.Serializer):
    question = QuestionSerializer(read_only=True)
    selected_alternative = AlternativeResultSerializer(read_only=True)
    correct_alternative = AlternativeResultSerializer(read_only=True)
    is_correct = serializers.BooleanField()


class ExamAnswerSummarySerializer(serializers.Serializer):
    total_questions = serializers.IntegerField()
    correct_questions = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class ExamAnswerResultSerializer(serializers.Serializer):
    summary = ExamAnswerSummarySerializer()
    question_answers = QuestionAnswerResultSerializer(many=True)
