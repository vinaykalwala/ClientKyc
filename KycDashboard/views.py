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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import KYCProperty
from .forms import KYCPropertyForm

from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import KYCProperty
from .models import CustomUser

@login_required
def kyc_list(request):
    # Fetch the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # If the logged-in user is a superuser, display all KYC properties
    if request.user.is_superuser:
        properties = KYCProperty.objects.all().order_by('-id')
    elif request.user.employee_type == "associate":
        properties = KYCProperty.objects.filter(file_maintained_by=request.user).order_by('-id')
    else:
        # Otherwise, only display KYC properties filed by the current user
        properties = KYCProperty.objects.filter(filed_by=request.user).order_by('-id')
    
    # Apply filtering based on search fields if search query is provided
    if search_query:
        properties = properties.filter(
            Q(client_name__icontains=search_query) |
            Q(village__icontains=search_query) |
            Q(site_number__icontains=search_query) |
            Q(sy_number__icontains=search_query) |
            Q(file_status__icontains=search_query)
        )
    
    return render(request, 'kyc_list.html', {
        'properties': properties,
        'search_query': search_query
    })


@login_required
def kyc_detail(request, pk):
    property = get_object_or_404(KYCProperty, pk=pk)
    return render(request, 'kyc_detail.html', {'property': property})

@login_required
def kyc_create(request):
    if request.method == "POST":
        form = KYCPropertyForm(request.POST)
        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.filed_by = request.user  # ensure 'filed_by' is correct
            kyc.save()
            return redirect('kyc_list')
        else:
            # Debugging form errors
            print(form.errors)  # Print errors to the console
    else:
        form = KYCPropertyForm()
    return render(request, 'kyc_form.html', {'form': form})

@login_required
def kyc_update(request, pk):
    # Fetch the KYC property using the provided primary key
    kyc = get_object_or_404(KYCProperty, pk=pk)
    
    # Permission check: Ensure the logged-in user is either the one who filed the property
    # or the one maintaining the property
    if kyc.filed_by != request.user and kyc.file_maintained_by != request.user:
        return HttpResponseForbidden('You do not have permission to edit this property.')

    if request.method == "POST":
        # If the user is the 'filed_by', allow editing the entire form
        if kyc.filed_by == request.user:
            form = KYCPropertyForm(request.POST, instance=kyc)
        # If the user is the 'file_maintained_by', allow editing only 'file_status' and 'status_remarks'
        elif kyc.file_maintained_by == request.user:
            form = KYCPropertyForm(request.POST, instance=kyc)
            form.fields['file_status'].required = True
            form.fields['status_remarks'].required = True
            # Disable other fields (this is optional based on your requirements)
            for field in form.fields:
                if field not in ['file_status', 'status_remarks']:
                    form.fields[field].disabled = True
        
        if form.is_valid():
            # Save the form but ensure 'filed_by' and 'file_maintained_by' are not modified
            kyc = form.save(commit=False)
            
            if kyc.filed_by != request.user:
                # If the current user is not the 'filed_by', we should not change the 'filed_by' field
                kyc.filed_by = kyc.filed_by  # Keep the 'filed_by' unchanged if not updating by 'filed_by' user
            
            kyc.save()
            return redirect('kyc_list')
    else:
        # If user is the 'filed_by', allow editing the entire form
        if kyc.filed_by == request.user:
            form = KYCPropertyForm(instance=kyc)
        # If user is the 'file_maintained_by', allow editing only 'file_status' and 'status_remarks'
        elif kyc.file_maintained_by == request.user:
            form = KYCPropertyForm(instance=kyc)
            form.fields['file_status'].required = True
            form.fields['status_remarks'].required = True
            # Disable other fields
            for field in form.fields:
                if field not in ['file_status', 'status_remarks']:
                    form.fields[field].disabled = True

    return render(request, 'kyc_form.html', {'form': form})

@login_required
def kyc_delete(request, pk):
    kyc = get_object_or_404(KYCProperty, pk=pk)
    if kyc.filed_by != request.user:  # Permission check
        return HttpResponseForbidden('You do not have permission to delete this property.')

    if request.method == "POST":
        kyc.delete()
        return redirect('kyc_list')
    return render(request, 'kyc_confirm_delete.html', {'property': kyc})


from django.utils.timezone import now
from .models import LeaveRequest
from .forms import LeaveRequestForm

@login_required
def apply_leave(request):
    if request.method == "POST":
        form = LeaveRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.applicant = request.user  # Assign logged-in user as the applicant
            leave.save()
            return redirect('leave_list')
    else:
        form = LeaveRequestForm(user=request.user)

    return render(request, 'apply_leave.html', {'form': form})


@login_required
def leave_list(request):
    if request.user.is_superuser:
        leaves = LeaveRequest.objects.all()[::-1]  
    else:
        leaves = LeaveRequest.objects.filter(applicant=request.user)[::-1]

    return render(request, 'leave_list.html', {'leaves': leaves})


@login_required
def leave_approve_reject(request, leave_id, action):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.user.is_superuser:
        if action == "approve":
            leave.status = "Approved"
            leave.approved_on = now()
        elif action == "reject":
            leave.status = "Rejected"
        leave.save()

    return redirect('leave_list')



from django.utils.dateparse import parse_date
from django.db.models import Sum
@login_required
def leave_data(request):
    leaves = None
    total_days = 0
    applicant = None

    if request.method == "GET":
        # Search by date (users on leave)
        date_str = request.GET.get('date')
        # Search by applicant's leave history (search by username, month, and year)
        username = request.GET.get('username')
        month = request.GET.get('month')
        year = request.GET.get('year')

        # Searching for users on leave on a specific date
        if date_str:
            date = parse_date(date_str)
            if date:
                leaves = LeaveRequest.objects.filter(start_date__lte=date, end_date__gte=date, status='Approved')
        
        # Searching by applicant's leave history by username
        elif username:
            applicant = CustomUser.objects.filter(username=username).first()
            if applicant:
                leaves = LeaveRequest.objects.filter(applicant=applicant)
                total_days = leaves.aggregate(total_days=Sum('duration'))['total_days']

        # Searching by applicant's leave history by username, month, and year
        elif username and month and year:
            applicant = CustomUser.objects.filter(username=username).first()
            if applicant:
                leaves = LeaveRequest.objects.filter(applicant=applicant, start_date__month=month, start_date__year=year)
                total_days = leaves.aggregate(total_days=Sum('duration'))['total_days']

        # If no parameters, show all leaves
        else:
            leaves = LeaveRequest.objects.all()

    return render(request, 'leave_data.html', {
        'leaves': leaves,
        'total_days': total_days,
        'applicant': applicant,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Task
from .forms import TaskForm

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)  # Only superusers can create tasks
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user 
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'create_task.html', {'form': form})

from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def task_list(request):
    query = Q()

    # Get the search term and date filters from the GET request
    search_term = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if request.user.is_superuser:
        tasks = Task.objects.all().order_by('-id')
    else:
        tasks = Task.objects.filter(assigned_to=request.user).order_by('-id')

    # Search query logic for task_name, assigned_to, assigned_by, etc.
    if search_term:
        query &= Q(task_name__icontains=search_term) | \
                Q(assigned_to__username__icontains=search_term) | \
                Q(assigned_by__username__icontains=search_term) | \
                Q(survey_number__icontains=search_term) | \
                Q(status__icontains=search_term) | \
                Q(priority__icontains=search_term)

    # Date range filtering logic
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            query &= Q(start_date__gte=start_date_obj)
        except ValueError:
            pass  # If date is not in the correct format, ignore the filter

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query &= Q(end_date__lte=end_date_obj)
        except ValueError:
            pass  # If date is not in the correct format, ignore the filter

    # Apply filters to the queryset
    tasks = tasks.filter(query)

    return render(request, 'task_list.html', {'tasks': tasks, 'search_term': search_term, 'start_date': start_date, 'end_date': end_date})

@login_required
def update_task(request, task_id):
    # Fetch the task object using the provided task_id
    task = get_object_or_404(Task, id=task_id)

    # Permission check: Ensure the logged-in user is either the one who assigned the task
    # or the one assigned to the task
    if task.assigned_by != request.user and task.assigned_to != request.user:
        return HttpResponseForbidden('You do not have permission to edit this task.')

    if request.method == "POST":
        # If the user is the one who assigned the task, allow editing all fields
        if task.assigned_by == request.user:
            form = TaskForm(request.POST, instance=task)
        # If the user is assigned to the task, allow editing only 'status' and 'remarks'
        elif task.assigned_to == request.user:
            form = TaskForm(request.POST, instance=task)
            form.fields['status'].required = True
            form.fields['remarks'].required = True
            # Disable other fields (this is optional based on your requirements)
            for field in form.fields:
                if field not in ['status', 'remarks']:
                    form.fields[field].disabled = True
        
        if form.is_valid():
            # Save the form but ensure 'assigned_by' and 'assigned_to' are not modified
            task = form.save(commit=False)
            
            if task.assigned_by != request.user:
                # If the current user is not the 'assigned_by', we should not change the 'assigned_by' field
                task.assigned_by = task.assigned_by  # Keep the 'assigned_by' unchanged if not updating by 'assigned_by' user
            
            task.save()
            return redirect('task_list')
    else:
        # If the user is the one who assigned the task, allow editing all fields
        if task.assigned_by == request.user:
            form = TaskForm(instance=task)
        # If the user is assigned to the task, allow editing only 'status' and 'remarks'
        elif task.assigned_to == request.user:
            form = TaskForm(instance=task)
            form.fields['status'].required = True
            form.fields['remarks'].required = True
            # Disable other fields
            for field in form.fields:
                if field not in ['status', 'remarks']:
                    form.fields[field].disabled = True

    return render(request, 'update_task.html', {'form': form, 'task': task})



from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def user_list(request):
    # Fetch all CustomUser objects excluding superusers
    users = CustomUser.objects.all().exclude(is_superuser=True)
    
    # Get the EMPLOYEE_CHOICES to pass to the template
    employee_choices = CustomUser.EMPLOYEE_CHOICES  # Get the employee types

    # Pass the users and choices to the template
    return render(request, 'user_list.html', {
        'users': users,
        'is_superuser': request.user.is_superuser,
        'employee_choices': employee_choices
    })



@staff_member_required
def delete_user(request, user_id):
    # Fetch the user to delete
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()  # Delete the user

    # Redirect to user list after deletion
    return redirect('user_list')  


from django.shortcuts import render
import os
from django.conf import settings

def log_viewer(request):
    log_file = os.path.join(settings.BASE_DIR, 'activity_logs.log')
    search_user = request.GET.get('user', '').lower()
    search_date = request.GET.get('date', '')

    with open(log_file, 'r') as file:
        logs = file.readlines()[::-1]

    # Filter logs
    if search_user:
        logs = [log for log in logs if search_user in log.lower()]
    if search_date:
        logs = [log for log in logs if search_date in log]

    return render(request, 'log_viewer.html', {'logs': logs})
