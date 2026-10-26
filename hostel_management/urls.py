from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from dashboard import views as dashboard_views
from dashboard import admin_views

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('admin-dashboard/', dashboard_views.admin_dashboard, name='admin_dashboard_direct'),
    path('warden/dashboard/', dashboard_views.warden_dashboard, name='warden_dashboard_direct'),
    
    # Direct Admin Control Center routes
    path('admin/residents/', admin_views.resident_admin_list, name='admin_residents_direct'),
    path('admin/wardens/', admin_views.warden_list, name='admin_wardens_direct'),
    path('admin/hostels/', RedirectView.as_view(url='/hostel/', permanent=False)),
    path('admin/rooms/', RedirectView.as_view(url='/hostel/rooms/', permanent=False)),
    path('admin/payments/', RedirectView.as_view(url='/fees/', permanent=False)),
    path('admin/reports/', RedirectView.as_view(url='/reports/', permanent=False)),
    path('admin/leaves/', admin_views.leave_admin_list, name='admin_leaves_direct'),
    path('admin/notices/', admin_views.notice_admin_list, name='admin_notices_direct'),
    path('admin/settings/', admin_views.admin_settings, name='admin_settings_direct'),

    path('admin/', admin.site.urls),

    path('student/dashboard/', dashboard_views.student_dashboard, name='student_dashboard'),
    path('working-professional/dashboard/', dashboard_views.working_professional_dashboard, name='working_professional_dashboard'),
    path('government-employee/dashboard/', dashboard_views.government_employee_dashboard, name='government_employee_dashboard'),
    path('private-employee/dashboard/', dashboard_views.private_employee_dashboard, name='private_employee_dashboard'),
    path('business/dashboard/', dashboard_views.business_dashboard, name='business_dashboard'),
    path('job-seeker/dashboard/', dashboard_views.job_seeker_dashboard, name='job_seeker_dashboard'),
    path('other/dashboard/', dashboard_views.other_dashboard, name='other_dashboard'),
    path('students/', include('students.urls', namespace='students')),
    path('hostel/', include('hostel.urls', namespace='hostel')),
    path('allocations/', include('allocations.urls', namespace='allocations')),
    path('fees/', include('fees.urls', namespace='fees')),
    path('complaints/', include('complaints.urls', namespace='complaints')),
    path('visitors/', include('visitors.urls', namespace='visitors')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('reports/', include('reports.urls', namespace='reports')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'hostel_management.views.error_403'
handler404 = 'hostel_management.views.error_404'
handler500 = 'hostel_management.views.error_500'
