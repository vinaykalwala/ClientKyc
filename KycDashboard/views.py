from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.http import HttpResponseForbidden


def signup(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to create users.")

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password1 = form.cleaned_data.get('password1')
            password2 = form.cleaned_data.get('password2')

            # Validate inputs
            if password1 != password2:
                messages.error(request, "Passwords do not match.")
                return render(request, 'signup.html', {'form': form})

            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "Invalid email address.")
                return render(request, 'signup.html', {'form': form})

            # Use CustomUser model instead of User
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
                return render(request, 'signup.html', {'form': form})

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already associated with an account.")
                return render(request, 'signup.html', {'form': form})

            # Create and save the user
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')  # Using original password
            user = authenticate(username=username, password=password)
            
            if user is not None:
                messages.success(request, "User created successfully! User can now log in.")
                return redirect('signup')  # Redirect to the next page
        else:
            # Handle form errors if not valid
            messages.error(request, "Please correct the errors below.")
        
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('role_redirect')  # Redirect based on role
            else:
                form.add_error(None, 'Invalid credentials')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def role_redirect(request):
    if request.user.is_superuser:
        return redirect('superuser_dashboard')
    elif request.user.employee_type == 'employee':
        return redirect('employee_dashboard')
    elif request.user.employee_type == 'associate':
        return redirect('associate_dashboard')
    return redirect('')

from django.contrib.auth import logout


@login_required
def logout_view(request):
    # Clear the session data to ensure no sensitive data is retained
    logout(request)
    
    # Set cache control headers to prevent caching of sensitive pages
    response = redirect('login')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
def employee_dashboard(request):
    return render(request, 'employee_dashboard.html')

@login_required
def associate_dashboard(request):
    return render(request, 'associate_dashboard.html')

@login_required
def superuser_dashboard(request):
    return render(request, 'superuser_dashboard.html')
