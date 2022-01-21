from rest_framework import serializers
from django.contrib.auth.models import User
from polls.models import Poll, Question, Choice, Answer


class ChoiceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    poll_id = serializers.IntegerField(read_only=True)
    question_id = serializers.IntegerField(read_only=True)
    question_number = serializers.IntegerField(read_only=True)
    # number of a choice in a question
    number = serializers.SerializerMethodField()

    class Meta:
        model = Choice
        fields = ['id', 'number', 'text', 'question_number', 'question_id', 'poll_id', 'owner']

    @staticmethod
    def get_number(choice):
        question = Question.objects.get(pk=choice.question_id)
        choice.poll_id = question.poll_id
        choice.question_number = QuestionSerializer.get_number(question)
        choices = list(question.choices.all())
        for i in range(0, len(choices)):
            if choices[i].id == choice.id:
                return i + 1


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    poll_id = serializers.IntegerField(read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')

    # number of a question in a poll
    number = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'number', 'text', 'type', 'choices', 'poll_id', 'owner']

    @staticmethod
    def get_number(question):
        poll = Poll.objects.get(pk=question.poll_id)
        questions = list(poll.questions.all())
        for i in range(0, len(questions)):
            if questions[i].id == question.id:
                return i + 1

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        for c in choices_data:
            c['owner'] = validated_data['owner']
        question = Question.objects.create(**validated_data)
        choices = [Choice.objects.create(question=question, **c) for c in choices_data]
        question.choices.set(choices)
        return question


class PollSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Poll
        fields = ['id', 'title', 'dt_open', 'dt_close', 'description', 'questions', 'owner']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        poll = Poll.objects.create(**validated_data)
        for i, q in enumerate(questions_data):
            choices_data = q.pop('choices')
            q['owner'] = validated_data['owner']
            question = Question.objects.create(poll=poll, **q)
            choices = []

            for c in choices_data:
                c['owner'] = validated_data['owner']
                choices.append(Choice.objects.create(question=question, **c))

            question.choices.set(choices)
        return poll


class UserSerializer(serializers.ModelSerializer):
    polls = serializers.PrimaryKeyRelatedField(many=True, queryset=Poll.objects.all())
    questions = serializers.PrimaryKeyRelatedField(many=True, queryset=Question.objects.all())
    choices = serializers.PrimaryKeyRelatedField(many=True, queryset=Choice.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'polls', 'questions', 'choices']


class AnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.ReadOnlyField(source='question.id')
    poll_id = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source='user.id')
    user_name = serializers.ReadOnlyField(source='user.name')

    class Meta:
        model = Answer
        fields = ['id', 'question_id', 'data', 'poll_id', 'user_id', 'user_name']

    def get_poll_id(self, answer):
        return answer.question.poll_id

    def create(self, validated_data):
        is_anon = bool(validated_data.pop('is_anon'))
        if is_anon:
            validated_data['user_id'] = User.objects.get(username="anon")

        answer = Answer.objects.create(**validated_data)
        return answer
