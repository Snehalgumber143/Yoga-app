from django.contrib import admin
from home.models import Contact
from .models import Student, LegacyRecord, Attendance

admin.site.register(Student)
admin.site.register(LegacyRecord)
admin.site.register(Attendance)
admin.site.register(Contact)
# Register your models here.
