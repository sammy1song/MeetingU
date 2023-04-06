from django.contrib import admin
from .models import Giver, Universities, Receiver, User, Meeting

# Register your models here.
admin.site.register(User)
admin.site.register(Giver)
admin.site.register(Universities)
admin.site.register(Receiver)
admin.site.register(Meeting)

