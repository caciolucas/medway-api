from answer.serializers import AnswerExamSerializer, ExamAnswerResultSerializer
from answer.service import AnswerService
from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from exam.models import Exam
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class ExamViewSet(viewsets.GenericViewSet):
    queryset = Exam.objects.all()

    def get_serializer_class(self):
        if self.action == "answer":
            return AnswerExamSerializer
        if self.action == "results":
            return ExamAnswerResultSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(
        method="post",
        request_body=AnswerExamSerializer,
        responses={201: openapi.Response("Exam submitted successfully")},
        operation_summary="Answer exam",
        operation_description="Answer the exam with the student's responses",
    )
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

    @swagger_auto_schema(
        method="get",
        responses={200: ExamAnswerResultSerializer()},
        operation_summary="Get exam results",
        operation_description="Get the results of the exam",
        manual_parameters=[
            openapi.Parameter(
                "student_id",
                openapi.IN_QUERY,
                description="ID of the student",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
    )
    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        student = request.query_params.get("student_id")
        exam = self.get_object()
        results = AnswerService.get_exam_answer_results(exam, student)

        serializer = self.get_serializer(results)
        return Response(serializer.data, status=status.HTTP_200_OK)