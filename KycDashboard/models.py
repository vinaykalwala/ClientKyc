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
    sy_number = models.CharField(max_length=255,blank=True, null=True)
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
        blank=True
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
