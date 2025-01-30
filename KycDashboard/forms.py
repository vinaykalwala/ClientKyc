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
