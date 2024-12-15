from question.models import Alternative, Question
from rest_framework import serializers


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class AlternativeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        exclude = ("question", "is_correct")
