from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(KYCProperty)
admin.site.register(LeaveRequest)
admin.site.register(Task)
admin.site.register(Notification)
