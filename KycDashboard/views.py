from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm, EmployeeStatusForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.http import HttpResponseForbidden

def home(request):
    return render(request, 'home.html')


def signup(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to create users.")

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)  # Include request.FILES for profile picture

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

            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
                return render(request, 'signup.html', {'form': form})

            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already associated with an account.")
                return render(request, 'signup.html', {'form': form})

            # Save the user with profile picture
            user = form.save(commit=False)
            user.original_password = password1  # Save original password if needed
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']  # Handle image upload
            user.save()

            messages.success(request, "User created successfully! User can now log in.")
            return redirect('signup')  # Redirect to login instead of signup
        else:
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
from django.contrib.auth import get_user_model


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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
import pytz
from .forms import MonthYearForm
from .models import KYCProperty
from django.contrib.auth import get_user_model

@login_required
def employee_dashboard(request):
    logged_in_user = request.user
    today = datetime.now()
    current_year, current_month, current_day = today.year, today.month, today.day

    # Handle form submission for selecting a different month/year
    if request.method == "POST":
        form = MonthYearForm(request.POST)
        if form.is_valid():
            selected_year = int(form.cleaned_data['year'])
            selected_month = int(form.cleaned_data['month'])
        else:
            selected_year = current_year
            selected_month = current_month
    else:
        selected_year = current_year
        selected_month = current_month

    # Fetch employee's KYC filings for the selected month/year
    total_files_filed = KYCProperty.objects.filter(
        filed_by=logged_in_user, filed_on_date__year=selected_year, filed_on_date__month=selected_month
    ).count()

    # Fetch all employees' KYC filings for the selected month/year
    employees = get_user_model().objects.filter(employee_type='employee')
    employee_file_counts = {
        emp: KYCProperty.objects.filter(filed_by=emp, filed_on_date__year=selected_year, filed_on_date__month=selected_month).count()
        for emp in employees
    }

    # Rank employees based on the number of files filed
    sorted_employees = sorted(employee_file_counts.items(), key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (emp, count) in enumerate(sorted_employees) if emp == logged_in_user), "N/A")

    # Assign a badge based on rank
    if rank == 1:
        badge = "Gold"
    elif rank == 2:
        badge = "Silver"
    elif rank == 3:
        badge = "Bronze"
    else:
        badge = "None"

    # Monthly filings for the selected month (1st to last day of the month)
    first_day_of_month = datetime(selected_year, selected_month, 1)
    last_day_of_month = datetime(selected_year, selected_month + 1, 1) - timedelta(days=1) if selected_month != 12 else datetime(selected_year, 12, 31)

    monthly_filing_data = [
        KYCProperty.objects.filter(filed_by=logged_in_user, filed_on_date=first_day_of_month + timedelta(days=i)).count()
        for i in range((last_day_of_month - first_day_of_month).days + 1)
    ]

    # Weekly filings (split the month into 4 weeks)
    weekly_data = []
    days_in_month = (last_day_of_month - first_day_of_month).days + 1
    weeks = [(0, 7), (7, 14), (14, 21), (21, days_in_month)]

    for start_day, end_day in weeks:
        week_start = first_day_of_month + timedelta(days=start_day)
        week_end = first_day_of_month + timedelta(days=end_day - 1)
        week_filings = KYCProperty.objects.filter(
            filed_by=logged_in_user,
            filed_on_date__gte=week_start,
            filed_on_date__lte=week_end
        ).count()
        weekly_data.append(week_filings)

    # Create the form for month/year selection
    form = MonthYearForm(initial={'year': str(selected_year), 'month': f"{selected_month:02}"})

    # Convert the current time to IST
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = today.astimezone(ist).strftime("%H:%M:%S")
    
    return render(request, 'employee_dashboard.html', {
        "form": form,
        "current_date": today.strftime("%Y-%m-%d"),
        "current_time": current_time_ist,
        "total_files_filed": total_files_filed,
        "rank": rank,
        "monthly_progress": (total_files_filed / max(max(employee_file_counts.values(), default=1), 1)) * 100 if total_files_filed > 0 else 0,# Calculate the progress
        "monthly_filing_data": monthly_filing_data,
        "weekly_data": weekly_data,
        "badge": badge,
        "weekly_chart_data": weekly_data,
        "monthly_chart_data": monthly_filing_data,
    })

@login_required
def associate_dashboard(request):
    logged_in_user = request.user

    # Get the year and month from the GET request, or set to current year/month if not present
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)
    
    # Convert year and month to integers
    year = int(year)
    month = int(month)

    # Initialize the form with the selected month and year
    form = MonthYearForm(initial={'month': str(month), 'year': str(year)})

    # Calculate total files maintained by the logged-in associate for the selected month
    total_files_maintained = KYCProperty.objects.filter(
        file_maintained_by=logged_in_user,
        filed_on_date__year=year,
        filed_on_date__month=month
    ).count()

    # Calculate total files completed by the associate for the selected month
    total_files_completed = KYCProperty.objects.filter(
        file_maintained_by=logged_in_user,
        file_status='completed',  # Ensure 'completed' status is considered
        filed_on_date__year=year,
        filed_on_date__month=month
    ).count()

    # Calculate success rate as a percentage of files completed out of files maintained
    associate_success_rate = (total_files_completed / total_files_maintained) * 100 if total_files_maintained else 0

    # Fetch all associates and calculate their total maintained and completed files for the selected month and year
    associates = get_user_model().objects.filter(employee_type='associate')
    
    associate_completed_counts = {}
    associate_total_counts = {}  # Dictionary to store total files maintained by each associate

    for associate in associates:
        # Calculate total files maintained for each associate
        total_files = KYCProperty.objects.filter(
            file_maintained_by=associate,
            filed_on_date__year=year,
            filed_on_date__month=month
        ).count()
        associate_total_counts[associate] = total_files
        
        # Calculate completed files for each associate
        completed_files = KYCProperty.objects.filter(
            file_maintained_by=associate,
            file_status='completed',
            filed_on_date__year=year,
            filed_on_date__month=month
        ).count()
        associate_completed_counts[associate] = completed_files

    # Only proceed with ranking if there are completed files
    if total_files_completed > 0:
        # Rank the logged-in associate based on total files completed
        sorted_associates = sorted(associate_completed_counts.items(), key=lambda x: x[1], reverse=True)
        rank = next((i + 1 for i, (associate, count) in enumerate(sorted_associates) if associate == logged_in_user), "N/A")

        # Assign a badge based on rank
        if rank == 1:
            badge = "Gold"
        elif rank == 2:
            badge = "Silver"
        elif rank == 3:
            badge = "Bronze"
        else:
            badge = "None"
    else:
        # No completed files, so set rank and badge to None
        rank = "N/A"
        badge = "None"

    # Monthly progress for the logged-in associate: Completed files each day
    first_day_of_month = datetime(year, month, 1)
    last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1) if month != 12 else datetime(year, 12, 31)

    # Monthly filings data (files completed on each day of the month)
    monthly_filing_data = [
        KYCProperty.objects.filter(
            file_maintained_by=logged_in_user,
            filed_on_date=first_day_of_month + timedelta(days=i),
            file_status='completed'
        ).count()
        for i in range((last_day_of_month - first_day_of_month).days + 1)
    ]

    # Weekly progress (completed files per week)
    weekly_data = []
    days_in_month = (last_day_of_month - first_day_of_month).days + 1
    weeks = [(0, 7), (7, 14), (14, 21), (21, days_in_month)]

    for start_day, end_day in weeks:
        week_start = first_day_of_month + timedelta(days=start_day)
        week_end = first_day_of_month + timedelta(days=end_day - 1)
        week_filings = KYCProperty.objects.filter(
            file_maintained_by=logged_in_user,
            filed_on_date__gte=week_start,
            filed_on_date__lte=week_end,
            file_status='completed'  # Only count completed files
        ).count()
        weekly_data.append(week_filings)

    # Weekly progress as a percentage (completed files per week)
    total_files_completed_for_week = sum(weekly_data)
    weekly_progress = [
        (weekly_data[i] / total_files_completed_for_week) * 100 if total_files_completed_for_week else 0
        for i in range(4)
    ]

    # Pass the context to the template for rendering
    return render(request, 'associate_dashboard.html', {
        'form': form,
        'success_rate': {
            'total_files_maintained': total_files_maintained,
            'total_files_completed': total_files_completed,
            'success_rate': associate_success_rate
        },
        'rank': rank,
        'monthly_filing_data': monthly_filing_data,  # Pass the monthly filing data to template
        'weekly_progress': weekly_progress,
        'badge': badge,
        'weekly_chart_data': weekly_data,
        'associate_file_counts': associate_total_counts,  # Pass the associate maintained file counts to the template
        'associate_completed_counts': associate_completed_counts,  # Pass completed file counts too
    })

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
from datetime import datetime
from calendar import monthrange
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import KYCProperty  # Assuming your model is in the same app

@login_required
def superuser_dashboard(request):
    # Get the year and month from the request (defaults to current month and year)
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)

    # Convert to integers
    year = int(year)
    month = int(month)

    logged_in_user = request.user
    success_rate_data = {}

    # If user is superuser, show the superuser dashboard
    if logged_in_user.is_superuser:
        # Calculate success rates for all users
        users = get_user_model().objects.all()

        # Data for employee comparison
        employee_comparison = {}

        # Day-by-day and Weekly reports
        day_report = defaultdict(int)
        weekly_report = defaultdict(int)

        # Get the number of days in the selected month
        _, num_days_in_month = monthrange(year, month)

        for user in users:
            if user.employee_type == 'associate':
                # Success rate calculation for associates
                total_files_maintained = KYCProperty.objects.filter(
                    file_maintained_by=user,
                    filed_on_date__year=year,
                    filed_on_date__month=month
                ).count()

                total_files_completed = KYCProperty.objects.filter(
                    file_maintained_by=user,
                    file_status='completed',
                    filed_on_date__year=year,
                    filed_on_date__month=month
                ).count()

                associate_success_rate = (total_files_completed / total_files_maintained) * 100 if total_files_maintained else 0

                success_rate_data[user.username] = {
                    'employee_type': user.employee_type,
                    'total_files_maintained': total_files_maintained,
                    'total_files_completed': total_files_completed,
                    'success_rate': associate_success_rate
                }

                # Day-by-day report for associates
                for day in range(1, num_days_in_month + 1):  # Ensure day is within the valid range
                    try:
                        # Check if day is valid within the month
                        day_start = datetime(year, month, day, 0, 0, 0)
                        day_end = datetime(year, month, day, 23, 59, 59)

                        daily_count = KYCProperty.objects.filter(
                            file_maintained_by=user,
                            filed_on_date__gte=day_start,
                            filed_on_date__lte=day_end
                        ).count()

                        day_report[day] += daily_count
                    except ValueError:
                        # If the day is invalid (e.g., 31st Feb), skip to next
                        continue

                # Weekly report for associates
                for week_num in range(1, 6):  # assuming 5 weeks in a month
                    try:
                        start_day = (week_num - 1) * 7 + 1
                        start_of_week = datetime(year, month, start_day)
                        # Check for valid end of the week
                        end_of_week = start_of_week + timedelta(days=6)

                        # Ensure end_of_week does not exceed the last valid day of the month
                        _, num_days_in_month = monthrange(year, month)
                        if end_of_week.day > num_days_in_month:
                            end_of_week = datetime(year, month, num_days_in_month)

                        weekly_count = KYCProperty.objects.filter(
                            file_maintained_by=user,
                            filed_on_date__gte=start_of_week,
                            filed_on_date__lte=end_of_week
                        ).count()

                        weekly_report[week_num] += weekly_count
                    except ValueError:
                        # Skip weeks if any calculation throws ValueError (invalid date)
                        continue

            elif user.employee_type == 'employee':
                # Success rate calculation for employees
                employee_file_counts = KYCProperty.objects.filter(
                    filed_by=user,
                    filed_on_date__year=year,
                    filed_on_date__month=month
                ).count()

                # Find the employee who filed the most files in the selected month/year
                employees = get_user_model().objects.filter(employee_type='employee')
                employee_file_counts_dict = {}
                for employee in employees:
                    employee_file_counts_dict[employee] = KYCProperty.objects.filter(
                        filed_by=employee,
                        filed_on_date__year=year,
                        filed_on_date__month=month
                    ).count()

                max_files_filed = max(employee_file_counts_dict.values(), default=0)

                success_rate = (employee_file_counts / max_files_filed) * 100 if max_files_filed > 0 else 0

                employee_comparison[user.username] = {
                    'employee_type': user.employee_type,
                    'total_files_filed': employee_file_counts,
                    'success_rate': success_rate
                }

        # Sort associates by success rate (descending) and employees by the number of files filed (descending)
        sorted_associates = sorted(success_rate_data.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        sorted_employees = sorted(employee_comparison.items(), key=lambda x: x[1]['total_files_filed'], reverse=True)

        # Generate Graph for Day-by-Day Report
        def generate_graph(data, x_labels, title, xlabel, ylabel, graph_type='line'):
            fig, ax = plt.subplots()

            if graph_type == 'line':
                ax.plot(x_labels, data, marker='o', linestyle='-', color='b')
            elif graph_type == 'bar':
                ax.bar(x_labels, data, color='g')

            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)

            # Save graph as image to be displayed in template
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format='png')
            img_buf.seek(0)
            img_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')

            return img_base64

        day_report_img = generate_graph(
            list(day_report.values()), list(day_report.keys()),
            "Day-by-Day Report", "Day", "Files Processed", "line"
        )

        weekly_report_img = generate_graph(
            list(weekly_report.values()), [f"Week {week}" for week in weekly_report.keys()],
            "Weekly Report", "Week", "Files Processed", "bar"
        )

        # Render the superuser dashboard with success rate data, day-wise and week-wise reports
        return render(request, 'superuser_dashboard.html', {
            'success_rate_data': sorted_associates,
            'employee_comparison': sorted_employees,
            'day_report': dict(day_report),
            'weekly_report': dict(weekly_report),
            'year': year,
            'month': month,
            'day_report_img': day_report_img,
            'weekly_report_img': weekly_report_img
        })

    return redirect('')


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
        form = KYCPropertyForm(request.POST,request.FILES)
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

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from .models import KYCProperty
from .forms import KYCPropertyForm

@login_required
def kyc_update(request, pk):
    # Fetch the KYC property using the provided primary key
    kyc = get_object_or_404(KYCProperty, pk=pk)

    # Allow superusers to edit everything
    if request.user.is_superuser:
        form = KYCPropertyForm(request.POST or None,request.FILES or None, instance=kyc)
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect('kyc_list')
        return render(request, 'kyc_form.html', {'form': form})

    # Permission check: Ensure the logged-in user is either the one who filed the property
    # or the one maintaining the property
    if kyc.filed_by != request.user and kyc.file_maintained_by != request.user:
        return HttpResponseForbidden('You do not have permission to edit this property.')

    if request.method == "POST":
        # If the user is the 'filed_by', allow editing the entire form
        if kyc.filed_by == request.user:
            form = KYCPropertyForm(request.POST, request.FILES ,instance=kyc)
        # If the user is the 'file_maintained_by', allow editing only 'file_status' and 'status_remarks'
        elif kyc.file_maintained_by == request.user:
            form = KYCPropertyForm(request.POST, instance=kyc)
            form.fields['file_status'].required = True
            form.fields['status_remarks'].required = True
            # Disable other fields
            for field in form.fields:
                if field not in ['file_status', 'status_remarks']:
                    form.fields[field].disabled = True
        
        if form.is_valid():
            kyc = form.save(commit=False)
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
                if field not in ['file_status', 'status_remarks','legal_opinion_doc']:
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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
                leaves = LeaveRequest.objects.filter(
                    start_date__lte=date, 
                    end_date__gte=date, 
                    status='Approved'
                )
        
        # Searching by applicant's leave history by username
        elif username:
            applicant = CustomUser.objects.filter(username=username).first()
            if applicant:
                leaves = LeaveRequest.objects.filter(applicant=applicant, status='Approved')
                total_days = leaves.aggregate(total_days=Sum('duration'))['total_days'] or 0

        # Searching by applicant's leave history by username, month, and year
        elif username and month and year:
            applicant = CustomUser.objects.filter(username=username).first()
            if applicant:
                leaves = LeaveRequest.objects.filter(
                    applicant=applicant, 
                    start_date__month=month, 
                    start_date__year=year, 
                    status='Approved'
                )
                total_days = leaves.aggregate(total_days=Sum('duration'))['total_days'] or 0

        # If no parameters, show all approved leaves
        else:
            leaves = LeaveRequest.objects.filter(status='Approved')

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
    survey_number = request.GET.get('survey_number', '')
    if request.method == 'POST':
        form = TaskForm(request.POST,survey_number=survey_number)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user 
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm(survey_number=survey_number)
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
            form.fields['work_done'].required = True
            form.fields['remarks'].required = True
            form.fields['task_status'].required=True
            # Disable other fields (this is optional based on your requirements)
            for field in form.fields:
                if field not in ['task_status','work_done', 'remarks']:
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
            form.fields['work_done'].required = True
            form.fields['remarks'].required = True
            form.fields['task_status'].required=True
            # Disable other fields
            for field in form.fields:
                if field not in ['task_status','work_done', 'remarks']:
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
from django.http import HttpResponse

@user_passes_test(lambda u: u.is_superuser)
@staff_member_required
def log_viewer(request):
    log_file = os.path.join(settings.BASE_DIR, 'activity_logs.log')
    search_user = request.GET.get('user', '').lower()
    search_date = request.GET.get('date', '')
    action = request.GET.get('action', '')

    # Handle log clearing
    if action == "clear":
        with open(log_file, 'w') as file:
            file.write("")  # Clear file contents
        return redirect('log_viewer')  # Reload the page

    # Read logs
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            logs = file.readlines()[::-1]  # Reverse logs for recent first

    # Filter logs
    if search_user:
        logs = [log for log in logs if search_user in log.lower()]
    if search_date:
        logs = [log for log in logs if search_date in log]

    # Handle printing logs
    if action == "print":
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="logs.txt"'
        response.writelines(logs)
        return response

    return render(request, 'log_viewer.html', {'logs': logs})



@login_required
def edit_employee_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        form = EmployeeStatusForm(request.POST, request.FILES, instance=user)  # Handle files
        if form.is_valid():
            form.save()
            messages.success(request, "Employee status and profile picture updated successfully.")
            return redirect('user_list')  # Redirect back to the list

    else:
        form = EmployeeStatusForm(instance=user)

    return render(request, 'edit_employee_status.html', {'form': form, 'user': user})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .models import KYCProperty

def user_portfolio(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)

    if user.employee_type == 'employee':
        kyc_records = KYCProperty.objects.filter(filed_by=user)
    elif user.employee_type == 'associate':
        kyc_records = KYCProperty.objects.filter(file_maintained_by=user)
    else:
        kyc_records = KYCProperty.objects.none()

    context = {
        'user': user,
        'kyc_records': kyc_records,
    }
    return render(request, 'user_portfolio.html', context)
