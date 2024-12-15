from answer.serializers import AnswerExamSerializer
from django.db import transaction
from exam.models import Exam
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class ExamViewSet(viewsets.GenericViewSet):
    queryset = Exam.objects.all()

    def get_serializer_class(self):
        if self.action == "answer":
            return AnswerExamSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        serializer = AnswerExamSerializer(
            data=request.data, context={"exam": self.get_object()}
        )
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    exam_response = serializer.save()
                    return Response(
                        {
                            "message": "Exam submitted successfully",
                            "id": exam_response.id,
                        },
                        status=status.HTTP_201_CREATED,
                    )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
