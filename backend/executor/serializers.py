

from rest_framework import serializers
from .models import Question, TestCase, Topic, Company

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = '__all__'

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name']

class QuestionSerializer(serializers.ModelSerializer):
    test_cases = TestCaseSerializer(many=True, read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    companies = CompanySerializer(many=True, read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)  # ✅ Add this line

    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'description',
            'sample_input',
            'sample_output',
            'explanation',
            'max_score',
            'difficulty',
            'difficulty_display',  # ✅ Include it in the output
            'topics',
            'companies',
            'year_asked',
            'test_cases',
        ]

class GenerateQuestionInputSerializer(serializers.Serializer):
    topic = serializers.CharField()
    difficulty = serializers.ChoiceField(choices=["Easy", "Medium", "Hard"])
