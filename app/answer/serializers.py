from answer.models import ExamAnswer, QuestionAnswer
from answer.tasks import evaluate_exam
from django.db import transaction
from question.models import Alternative, Question
from rest_framework import serializers
from student.models import Student

# NOTE: Could also use a ModelSerializer but I'll use a Serializer to have more control over the fields.

# NOTE: Could also add the business logic in a AnswerService class, but to avoid spreading the logic, I'll leave it here.


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

    @transaction.atomic
    def create(self, validated_data):
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

        evaluate_exam(exam_response.id)
        # NOTE: Could also trigger this in a signal. But to center all business logic in the serializer, I'll leave it here.
        # NOTE: Adding a retry policy to avoid overloading the system in case of a failure.
        # evaluate_exam.apply_async(
        #     args=(exam_response.id,),
        #     retry=True,
        #     retry_policy={
        #         "max_retries": 3,
        #         "interval_start": 0,
        #         "interval_step": 0.2,
        #         "interval_max": 0.5,
        #     },
        # )

        return exam_response
