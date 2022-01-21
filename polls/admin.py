from django.contrib import admin
from polls.models import Poll, Question, Choice, Answer


class PollAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('dt_open',)
        else:
            return ()


admin.site.register(Poll, PollAdmin)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Answer)
