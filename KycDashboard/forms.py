from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    employee_type = forms.ChoiceField(choices=CustomUser.EMPLOYEE_CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'password1', 'password2', 'employee_type'
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

class KYCPropertyForm(forms.ModelForm):
    class Meta:
        model = KYCProperty
        fields = '__all__'
        exclude = ['filed_by']
        widgets = {
            'file_status': forms.Select(choices=KYCProperty.FILE_STATUS_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the choices for the 'file_maintained_by' field to only associates
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
