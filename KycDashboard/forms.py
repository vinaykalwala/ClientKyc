from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Task

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    employee_type = forms.ChoiceField(choices=CustomUser.EMPLOYEE_CHOICES, required=True)
    profile_picture = forms.ImageField(required=False)
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number','employee_status',
            'password1', 'password2', 'employee_type','profile_picture'
        ]
        help_texts = {  
            'username': '',
            'password1': '',
            'password2': '',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.original_password = self.cleaned_data['password1']  # Store original password
        if commit:
            user.save()
        return user


from django import forms
from .models import KYCProperty
from django.contrib.auth import get_user_model

from django.contrib.auth import get_user_model

class KYCPropertyForm(forms.ModelForm):
    class Meta:
        model = KYCProperty
        fields = '__all__'  
        exclude = ['filed_by']  
        widgets = {
            'file_status': forms.Select(choices=KYCProperty.FILE_STATUS_CHOICES),
            'file_returned_date':forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'sy_number': 'Survey Number',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically filter the 'file_maintained_by' field queryset
        self.fields['file_maintained_by'].queryset = get_user_model().objects.filter(employee_type='associate')


from django import forms
from .models import LeaveRequest

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'handover_document', 'relief_officer']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'handover_document': forms.FileInput(attrs={'class': 'form-control'}),
            'relief_officer': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(LeaveRequestForm, self).__init__(*args, **kwargs)
        
        # Filter relief officer choices to only superusers
        self.fields['relief_officer'].queryset = LeaveRequest._meta.get_field('relief_officer').remote_field.model.objects.filter(is_superuser=True)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['survey_number', 'task_name', 'task_description', 'assigned_to', 'start_date', 'end_date', 'priority','task_status','work_done','remarks']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        survey_number = kwargs.pop('survey_number', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        if survey_number:
            self.fields['survey_number'].initial = survey_number
        self.fields['assigned_to'].queryset = CustomUser.objects.exclude(is_staff=True)

from django import forms
import datetime

class MonthYearForm(forms.Form):
    current_year = datetime.date.today().year
    month = forms.ChoiceField(
        choices=[(str(i), f"{i:02}") for i in range(1, 13)], 
        label='Month',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(current_year - 10, current_year + 11)], 
        label='Year',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

from django import forms
from .models import CustomUser

class EmployeeStatusForm(forms.ModelForm):
    EMPLOYEE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    employee_status = forms.ChoiceField(choices=EMPLOYEE_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['employee_status','profile_picture']
