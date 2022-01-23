from datetime import datetime

from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
from django.http import Http404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from .models import Poll, Question, Answer
from .serializers import PollSerializer, QuestionSerializer, ChoiceSerializer, UserSerializer, AnswerSerializer
from .permissions import IsOwnerOrReadOnly


class UserList(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser,
                          IsOwnerOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser,
                          IsOwnerOrReadOnly]
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

    @staticmethod
    def validate_poll_request(user: User, poll_id: int):
        if isinstance(user, AnonymousUser):
            return None, status.HTTP_401_UNAUTHORIZED

        try:
            poll = Poll.objects.get(pk=poll_id)
        except Poll.DoesNotExist:
            raise Http404

        if poll.dt_close < timezone.now() and not user.is_staff:
            return None, status.HTTP_403_FORBIDDEN

        return poll, status.HTTP_200_OK

    def retrieve(self, request, *args, **kwargs):
        poll, status_code = self.validate_poll_request(request.user, kwargs.get('pk'))
        return Response(data=PollSerializer(poll).data, status=status_code)

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save(owner=self.request.user)


class PollQuestionList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly]

    def get(self, request, poll_id):
        poll, status_code = PollDetail.validate_poll_request(request.user, poll_id)
        if not poll:
            return Response(data=PollSerializer(poll).data, status=status_code)

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
    def get_question(poll, question_number: int):
        try:
            return poll.questions.all()[question_number - 1]
        except IndexError:
            raise Http404

    def get(self, request, poll_id, question_number):
        poll, status_code = PollDetail.validate_poll_request(request.user, poll_id)
        if not poll:
            return Response(data=PollSerializer(poll).data, status=status_code)

        question = self.get_question(poll, question_number)
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
        poll, status_code = PollDetail.validate_poll_request(request.user, poll_id)
        if not poll:
            return Response(data=poll, status=status_code)

        question = PollQuestionDetail.get_question(poll, question_number)
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
    def get_choice(poll: Poll(), question_number: int, choice_number):
        try:
            question = PollQuestionDetail.get_question(poll, question_number)
            return question.choices.all()[choice_number - 1]
        except IndexError:
            return Http404

    def get(self, request, poll_id, question_number, choice_number):
        poll, status_code = PollDetail.validate_poll_request(request.user, poll_id)
        if not poll:
            return Response(data=poll, status=status_code)

        choice = self.get_choice(poll_id, question_number, choice_number)
        serializer = ChoiceSerializer(choice)
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

    @staticmethod
    def choices_valid(actual: Question, submitted):
        actual = set([str(c['id']) for c in actual.choices.values()])
        print(actual)
        submitted = set(submitted.data.get('data').keys())
        return len(submitted.difference(actual)) == 0

    def post(self, request, question_id):
        question = Question.objects.get(pk=question_id)

        if not self.choices_valid(question, request):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = AnswerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(question=question, user=request.user,
                            is_anon=bool(request.data.get('is_anon')))
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
            return Response(data={"detail": "No data found for this user."}, status=status.HTTP_400_BAD_REQUEST)

