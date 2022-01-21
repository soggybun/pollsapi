from datetime import datetime

from .models import Poll, Question, Answer
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from .serializers import PollSerializer, QuestionSerializer, ChoiceSerializer, UserSerializer, AnswerSerializer
from .permissions import IsOwnerOrReadOnly


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PollList(generics.ListCreateAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    def list(self, request, *args, **kwargs):
        polls_filtered = self.queryset.all() if request.user.is_staff \
            else self.queryset.all().filter(dt_close__gt=datetime.now())
        serializer = PollSerializer(polls_filtered, many=True)
        return Response(data=serializer.data)

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save(owner=self.request.user)


class PollDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save(owner=self.request.user)


class PollQuestionList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    @staticmethod
    def get_poll(poll_id):
        try:
            return Poll.objects.get(pk=poll_id)
        except (Poll.DoesNotExist, Question.DoesNotExist):
            raise Http404

    def get(self, request, poll_id):
        poll = self.get_poll(poll_id)
        serializer = QuestionSerializer(poll.questions, many=True)
        return Response(serializer.data)

    @staticmethod
    def post(request, poll_id):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['poll_id'] = poll_id
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PollQuestionDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    @staticmethod
    def get_question(poll_id: int, question_number: int):
        try:
            poll = Poll.objects.get(pk=poll_id)
            return poll.questions.all()[question_number - 1]
        except (Poll.DoesNotExist, IndexError):
            raise Http404

    def get(self, request, poll_id, question_number):
        question = self.get_question(poll_id, question_number)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)

    def delete(self, request, poll_id, question_number):
        self.get_question(poll_id, question_number).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, poll_id, question_number):
        try:
            question = self.get_question(poll_id, question_number)
            serializer = QuestionSerializer(question, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(owner=request.user)
                return Response(serializer.data, status.HTTP_202_ACCEPTED)
        except IndexError:
            return PollQuestionList.post(request, poll_id)
        except Poll.DoesNotExist:
            raise Http404
        return Response(status=status.HTTP_400_BAD_REQUEST)


class QuestionChoiceList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    def get(self, request, poll_id, question_number):
        question = PollQuestionDetail.get_question(poll_id, question_number)
        serializer = ChoiceSerializer(question.choices, many=True)
        return Response(data=serializer.data)

    @staticmethod
    def post(request, poll_id, question_number):
        serializer = ChoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['question_id'] = PollQuestionDetail.get_question(poll_id, question_number).id
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionChoiceDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    @staticmethod
    def get_choice(poll_id: int, question_number: int, choice_number):
        try:
            question = PollQuestionDetail.get_question(poll_id, question_number)
            return question.choices.all()[choice_number - 1]
        except IndexError:
            return Http404

    def get(self, request, poll_id, question_number, choice_number):
        question = self.get_choice(poll_id, question_number, choice_number)
        serializer = ChoiceSerializer(question)
        return Response(serializer.data)

    def delete(self, request, poll_id, question_number, choice_number):
        self.get_choice(poll_id, question_number, choice_number).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, poll_id, question_number, choice_number):
        try:
            choice = self.get_choice(poll_id, question_number, choice_number)
            serializer = ChoiceSerializer(choice, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(owner=request.user)
                return Response(serializer.data, status.HTTP_202_ACCEPTED)
        except IndexError:
            return QuestionChoiceList.post(request, poll_id, question_number)
        except Poll.DoesNotExist:
            raise Http404


class AnswerDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def choices_valid(self, actual: Question, submitted):
        actual = set([str(c['id']) for c in actual.choices.values()])
        submitted = set(submitted.data.get('data').keys())
        return len(submitted.symmetric_difference(actual)) == 0

    def post(self, request, question_id):
        question = Question.objects.get(pk=question_id)

        if not self.choices_valid(question, request):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = AnswerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(question=question, user=request.user,
                            is_anon=bool(request.data.get('is_anon')), poll_id=question.poll_id)
        return Response(status=status.HTTP_200_OK)


class AnswerList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user_answers = Answer.objects.all() if request.user.is_staff \
                else Answer.objects.filter(user__id=request.user.id)
            serializer = AnswerSerializer(user_answers, many=True)
            return Response(data=serializer.data)
        except Answer.DoesNotExist:
            return Response(data={"Reason": "No data for this user."}, status=status.HTTP_400_BAD_REQUEST)

