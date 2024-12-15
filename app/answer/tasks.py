import logging

from answer.models import ExamAnswer
from celery import shared_task
from django.db import transaction

logger = logging.getLogger("django")

@shared_task()
def evaluate_exam(exam_answer_id: int):
    try:
        with transaction.atomic():
            logger.info(f"Evaluating exam answer {exam_answer_id}")
            exam_answer = ExamAnswer.objects.select_for_update().get(id=exam_answer_id)
            exam_answer.status = ExamAnswer.PROCESSING
            exam_answer.save()

            for question_answer in exam_answer.question_responses.all():
                question_answer.is_correct = (
                    question_answer.selected_alternative.is_correct
                )
                question_answer.save()

            logger.info(f"Exam answer {exam_answer_id} evaluated")
            exam_answer.status = ExamAnswer.EVALUATED
            exam_answer.save()
    except Exception as e:
        exam_answer = ExamAnswer.objects.get(id=exam_answer_id)
        exam_answer.status = ExamAnswer.PENDING
        exam_answer.save()
        raise e
