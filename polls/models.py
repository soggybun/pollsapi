from django.db import models
from datetime import datetime, timedelta
from django.contrib.postgres.fields import JSONField


TEXT = 'TEXT'
CHOICE_SINGLE = 'CHOICE_SINGLE'
CHOICE_MULTIPLE = 'CHOICE_MULTIPLE'

QUESTION_TYPES = [(TEXT, 'text'), (CHOICE_SINGLE, 'choice_single'), (CHOICE_MULTIPLE, 'choice_multiple')]


class Poll(models.Model):
    title = models.CharField(max_length=100)  # blank = False?
    dt_open = models.DateTimeField(auto_now_add=True)
    dt_close = models.DateTimeField(blank=False, default=datetime.now()+timedelta(days=14))
    owner = models.ForeignKey('auth.User', related_name='polls', on_delete=models.CASCADE)
    description = models.TextField()

    class Meta:
        ordering = ['dt_close']


class Question(models.Model):
    poll = models.ForeignKey(Poll, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=250)
    type = models.CharField(choices=QUESTION_TYPES, default='text', max_length=50)
    users = models.ManyToManyField('auth.User', through='Answer')  # rel_name ?
    owner = models.ForeignKey('auth.User', related_name='questions', on_delete=models.CASCADE)


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=200, null=True)


class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', related_name='answers', on_delete=models.CASCADE)
    data = JSONField(blank=True, default=dict)
