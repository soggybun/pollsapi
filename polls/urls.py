from django.urls import path, include
from . import views

urlpatterns = [
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('polls/', views.PollList.as_view()),
    path('polls/<int:pk>/', views.PollDetail.as_view()),
    path('polls/<int:poll_id>/questions/', views.PollQuestionList.as_view()),
    path('polls/<int:poll_id>/questions/<int:question_number>/', views.PollQuestionDetail.as_view()),
    path('polls/<int:poll_id>/questions/<int:question_number>/choices/',
         views.QuestionChoiceList.as_view()),
    path('polls/<int:poll_id>/questions/<int:question_number>/choices/<int:choice_number>',
         views.QuestionChoiceDetail.as_view()),
    path('submit/<int:question_id>/', views.AnswerDetail.as_view()),
    path('submit/results/', views.AnswerList.as_view())
]

urlpatterns += [
    path('auth/', include('rest_framework.urls')),
]
