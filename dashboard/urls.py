from django.urls import path
from . import views
from . import admin_views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('warden/dashboard/', views.warden_dashboard, name='warden_dashboard'),

    # Warden Management
    path('admin/wardens/', admin_views.warden_list, name='admin_wardens'),
    path('admin/wardens/add/', admin_views.warden_create, name='admin_warden_create'),
    path('admin/wardens/<int:pk>/edit/', admin_views.warden_edit, name='admin_warden_edit'),
    path('admin/wardens/<int:pk>/toggle/', admin_views.warden_toggle_status, name='admin_warden_toggle'),
    path('admin/wardens/<int:pk>/reset-password/', admin_views.warden_reset_password, name='admin_warden_reset_password'),

    # Resident Management
    path('admin/residents/', admin_views.resident_admin_list, name='admin_residents'),

    # Leave Management
    path('admin/leaves/', admin_views.leave_admin_list, name='admin_leaves'),
    path('admin/leaves/<int:pk>/action/', admin_views.leave_action, name='admin_leave_action'),

    # Notice Management
    path('admin/notices/', admin_views.notice_admin_list, name='admin_notices'),
    path('admin/notices/add/', admin_views.notice_create, name='admin_notice_create'),
    path('admin/notices/<int:pk>/edit/', admin_views.notice_edit, name='admin_notice_edit'),
    path('admin/notices/<int:pk>/delete/', admin_views.notice_delete, name='admin_notice_delete'),

    # System Settings
    path('admin/settings/', admin_views.admin_settings, name='admin_settings'),

    # Resident Dashboards
    path('student/', views.student_dashboard, name='student'),
    path('working-professional/', views.working_professional_dashboard, name='working_professional'),
    path('government-employee/', views.government_employee_dashboard, name='government_employee'),
    path('private-employee/', views.private_employee_dashboard, name='private_employee'),
    path('business/', views.business_dashboard, name='business'),
    path('job-seeker/', views.job_seeker_dashboard, name='job_seeker'),
    path('other/', views.other_dashboard, name='other'),
]
