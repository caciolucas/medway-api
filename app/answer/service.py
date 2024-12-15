from answer.models import ExamAnswer
from question.models import Alternative


class AnswerService:
    @classmethod
    def __get_exam_answer_summary(cls, exam_answer: ExamAnswer):
        total_questions = exam_answer.exam.questions.count()
        correct_answers = exam_answer.question_responses.filter(is_correct=True).count()
        percentage = (correct_answers / total_questions) * 100

        summary = {
            "total_questions": total_questions,
            "correct_questions": correct_answers,
            "percentage": percentage,
        }
        return summary

    @classmethod
    def __get_exam_answer_question_results(cls, exam_answer: ExamAnswer):
        questions = []
        for question_answer in exam_answer.question_responses.all():
            correct_alternative = Alternative.objects.get(
                question=question_answer.question, is_correct=True
            )
            questions.append(
                {
                    "question": question_answer.question,
                    "selected_alternative": question_answer.selected_alternative,
                    "correct_alternative": correct_alternative,
                    "is_correct": question_answer.is_correct,
                }
            )

        return questions

    @classmethod
    def get_exam_answer_results(cls, exam_id: int, student_id: int):
        exam_answer = ExamAnswer.objects.get(exam_id=exam_id, student_id=student_id)

        summary = cls.__get_exam_answer_summary(exam_answer)

        questions = cls.__get_exam_answer_question_results(exam_answer)

        return {"summary": summary, "question_answers": questions}
