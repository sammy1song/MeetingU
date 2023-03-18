from django.contrib import admin
from .models import Giver, Universities, Receiver, User, Meeting, TimeSlot

# Register your models here.
admin.site.register(User)
admin.site.register(Giver)
admin.site.register(Universities)
admin.site.register(Receiver)
admin.site.register(Meeting)

class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'date', 'is_available')
    list_filter = ('date', 'is_available')
    search_fields = ('date',)

admin.site.register(TimeSlot, TimeSlotAdmin)