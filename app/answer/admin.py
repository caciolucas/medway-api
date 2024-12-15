from answer.models import ExamAnswer, QuestionAnswer
from django.contrib import admin

# Register your models here.


class QuestionAnswerInline(admin.TabularInline):
    model = QuestionAnswer


@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    inlines = [QuestionAnswerInline]
