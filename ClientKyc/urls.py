"""
URL configuration for ClientKyc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from KycDashboard.views import *
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', role_redirect, name='role_redirect'),
    path('employee-dashboard/', employee_dashboard, name='employee_dashboard'),
    path('associate-dashboard/', associate_dashboard, name='associate_dashboard'),
    path('superuser-dashboard/', superuser_dashboard, name='superuser_dashboard'),
    path('kyc_list', kyc_list, name='kyc_list'),
    path('kyc_detail/<int:pk>/', kyc_detail, name='kyc_detail'),
    path('kyc_create/', kyc_create, name='kyc_create'),
    path('kyc_update/<int:pk>/', kyc_update, name='kyc_update'),
    path('kyc_delete/<int:pk>/', kyc_delete, name='kyc_delete'),
    path('applyleave/', apply_leave, name='apply_leave'),
    path('leavelist/', leave_list, name='leave_list'),
    path('leaveapprovereject/<int:leave_id>/<str:action>/', leave_approve_reject, name='leave_approve_reject'),
    path('leave_data/', leave_data, name='leave_data'),
    path('createtask/', create_task, name='create_task'),
    path('tasklist/', task_list, name='task_list'),
    path('updatetask/<int:task_id>/', update_task, name='update_task'),
    path('user_list/', user_list, name='user_list'),
    path('delete_user/<int:user_id>/', delete_user, name='delete_user'),
    path('logs/', log_viewer, name='log_viewer'),
    path('edit-status/<int:user_id>/', edit_employee_status, name='edit_employee_status'),
    path('user/<int:user_id>/', user_portfolio, name='user_portfolio'),
    path('update_task_status/<int:task_id>/', update_task_status, name='update_task_status'),
    path('update_work_done/<int:task_id>/', update_work_done, name='update_work_done'),
    path('change-password/', change_password, name='change_password'),
    path('notifications/', notifications_view, name='notifications'),
    path('read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),
    path('read-all/', mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('notifications/read/', read_notifications_view, name='read_notifications'),
    path('notifications/delete-all-read/', delete_all_read_notifications, name='delete_all_read_notifications'),
     path('', landing, name='landing'),
    path('about/', about, name='about'),
    path('services/', services, name='services'),
    path('contact/',contact, name='contact'),
    path('consultation/',consultation, name='consultation'),
    path('consultation_submit_form/', consultation_submit_form, name='consultation_submit_form'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)