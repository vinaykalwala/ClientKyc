from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser
class CustomUser(AbstractUser):
    EMPLOYEE_CHOICES = (
    ('employee', 'Employee'),
    ('associate', 'Associate'),
)
    employee_type = models.CharField(
        max_length=10,
        choices=EMPLOYEE_CHOICES,
        
    )
    original_password = models.CharField(max_length=255)

    def __str__(self):
        return self.username
