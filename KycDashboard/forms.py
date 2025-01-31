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
