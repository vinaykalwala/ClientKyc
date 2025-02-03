from django.conf import settings
from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model

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


class KYCProperty(models.Model):
    client_name = models.CharField(max_length=255,blank=True, null=True)
    mobile_number = models.CharField(max_length=10,blank=True, null=True)
    whatsapp_number = models.CharField(max_length=10,blank=True, null=True)
    email_id = models.EmailField(blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    property_owner_pan = models.CharField(max_length=10,blank=True, null=True)
    mode_of_seller_ownership = models.CharField(max_length=255,blank=True, null=True)
    nature_of_property = models.CharField(max_length=255,blank=True, null=True)
    site_number = models.CharField(max_length=255,blank=True, null=True)
    sy_number = models.CharField(max_length=255,unique=True)
    village = models.CharField(max_length=255,blank=True, null=True)
    hobli = models.CharField(max_length=255,blank=True, null=True)
    taluk = models.CharField(max_length=255,blank=True, null=True)
    vacant_or_built = models.CharField(max_length=255,blank=True, null=True)
    localbody_or_katha = models.CharField(max_length=255,blank=True, null=True)
    conversion = models.CharField(max_length=255,blank=True, null=True)
    existing_loan = models.CharField(max_length=255,blank=True, null=True)
    rajakaluve_or_high_tension_wire_or_temple_or_grave_or_yard = models.CharField(max_length=255,blank=True, null=True)
    assessment_or_remarks = models.TextField(blank=True, null=True)
    summary_or_proceedings = models.TextField(blank=True, null=True)
    oral_or_written_opinion = models.TextField(blank=True, null=True)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    advance = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    file_maintained_by = models.ForeignKey(
        get_user_model(), 
        on_delete=models.SET_NULL, 
        limit_choices_to={'employee_type': 'associate'}, 
        related_name='maintained_files',
        null=True, 
    )
    filed_on_date = models.DateField(auto_now_add=True)
    filed_by = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name='filed_by_user'
    )
    FILE_STATUS_CHOICES = (
        ('assigned', 'Assigned'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('closed','Closed'),
    )
    file_status = models.CharField(
        max_length=10,
        choices=FILE_STATUS_CHOICES,
        default='assigned'
    )
    status_remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.client_name

from django.db import models
from django.conf import settings  # Import settings to access AUTH_USER_MODEL

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('Sick Leave', 'Sick Leave'),
        ('Casual Leave', 'Casual Leave'),
        ('Annual Leave', 'Annual Leave'),
        ('Maternity Leave', 'Maternity Leave'),
        ('Paternity Leave', 'Paternity Leave'),
        ('Other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use AUTH_USER_MODEL instead of auth.User
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.IntegerField()  # Auto-calculated duration
    reason = models.TextField()
    handover_document = models.FileField(upload_to='handover_docs/', blank=True, null=True)
    relief_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use AUTH_USER_MODEL instead of auth.User
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_superuser': True},
        related_name="relief_officer"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Automatically calculate duration before saving"""
        if self.start_date and self.end_date:
            self.duration = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.applicant} - {self.leave_type} ({self.status})"

from django.core.exceptions import ValidationError
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    survey_number = models.CharField(max_length=255)
    task_name = models.CharField(max_length=255)
    task_description = models.TextField()
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_tasks")
    start_date = models.DateField()
    end_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.task_name

    def clean(self):
        """ Validate that the entered survey_number exists in ClientKyc. """
        if not KYCProperty.objects.filter(sy_number=self.survey_number).exists():
            raise ValidationError({'survey_number': 'This survey number does not exist in Database.'})

        """ Validate assigned_to only allows users with employee_type 'Associate' """
        if not self.assigned_to.employee_type == 'associate':
            raise ValidationError({'assigned_to': 'Task can only be assigned to Associates.'})