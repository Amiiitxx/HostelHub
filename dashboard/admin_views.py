from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone

from accounts.models import User, WardenProfile
from students.models import Student
from hostel.models import Building, Room, Bed
from allocations.models import Allocation
from fees.models import Fee, Payment
from complaints.models import Complaint
from visitors.models import Visitor
from attendance.models import LeaveRequest
from .models import Notice
from .forms import WardenCreateForm, WardenEditForm, NoticeForm
from .security import admin_required


# ============================================================
# WARDEN MANAGEMENT
# ============================================================

@admin_required
def warden_list(request):
    """
    List all Wardens with assigned hostel, status, employee ID, and contact info.
    """
    wardens = WardenProfile.objects.select_related('user', 'assigned_hostel').all()
    
    total_wardens = wardens.count()
    active_wardens = wardens.filter(status='active').count()
    assigned_wardens = wardens.filter(assigned_hostel__isnull=False).count()

    context = {
        'wardens': wardens,
        'total_wardens': total_wardens,
        'active_wardens': active_wardens,
        'assigned_wardens': assigned_wardens,
        'unassigned_wardens': total_wardens - assigned_wardens,
    }
    return render(request, 'admin/wardens/list.html', context)


@admin_required
def warden_create(request):
    """
    Add a new Warden: creates User with role='warden' and WardenProfile.
    """
    if request.method == 'POST':
        form = WardenCreateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        role=User.ROLE_WARDEN,
                        phone=form.cleaned_data['phone'],
                        is_staff=True,
                    )
                    
                    WardenProfile.objects.create(
                        user=user,
                        employee_id=form.cleaned_data['employee_id'],
                        phone=form.cleaned_data['phone'],
                        assigned_hostel=form.cleaned_data['assigned_hostel'],
                        assigned_block=form.cleaned_data['assigned_block'],
                        status='active',
                        joining_date=form.cleaned_data['joining_date'],
                        profile_photo=form.cleaned_data.get('profile_photo'),
                    )

                messages.success(request, f"Warden {user.get_full_name()} created successfully!")
                return redirect('dashboard:admin_wardens')
            except Exception as e:
                messages.error(request, f"Failed to create warden: {str(e)}")
    else:
        form = WardenCreateForm()

    return render(request, 'admin/wardens/form.html', {
        'form': form,
        'title': 'Add New Warden',
        'action_label': 'Create Warden Account',
    })


@admin_required
def warden_edit(request, pk):
    """
    Edit Warden details and hostel assignment.
    """
    warden = get_object_or_404(WardenProfile.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        form = WardenEditForm(request.POST, request.FILES, instance=warden)
        if form.is_valid():
            with transaction.atomic():
                warden_inst = form.save()
                user = warden_inst.user
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.email = form.cleaned_data['email']
                user.phone = form.cleaned_data['phone']
                user.is_active = (warden_inst.status == 'active')
                user.save()

            messages.success(request, f"Warden profile for {warden.full_name} updated successfully.")
            return redirect('dashboard:admin_wardens')
    else:
        form = WardenEditForm(instance=warden)

    return render(request, 'admin/wardens/form.html', {
        'form': form,
        'warden': warden,
        'title': f"Edit Warden: {warden.full_name}",
        'action_label': 'Update Warden Details',
    })


@admin_required
def warden_toggle_status(request, pk):
    """
    Activate / Deactivate Warden account.
    """
    warden = get_object_or_404(WardenProfile.objects.select_related('user'), pk=pk)
    if warden.status == 'active':
        warden.status = 'inactive'
        warden.user.is_active = False
        messages.warning(request, f"Warden {warden.full_name} deactivated.")
    else:
        warden.status = 'active'
        warden.user.is_active = True
        messages.success(request, f"Warden {warden.full_name} activated.")
    
    warden.save()
    warden.user.save()
    return redirect('dashboard:admin_wardens')


@admin_required
def warden_reset_password(request, pk):
    """
    Reset a Warden's password.
    """
    warden = get_object_or_404(WardenProfile.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password and len(new_password) >= 6:
            warden.user.set_password(new_password)
            warden.user.save()
            messages.success(request, f"Password for {warden.full_name} has been reset successfully.")
        else:
            messages.error(request, "Password must be at least 6 characters long.")
    return redirect('dashboard:admin_wardens')


# ============================================================
# RESIDENT MANAGEMENT (ADMIN VIEW)
# ============================================================

@admin_required
def resident_admin_list(request):
    """
    Admin resident directory with comprehensive filtering:
    Occupation, Hostel, Room, Payment Status, and Search.
    """
    residents = Student.objects.select_related('user').all()

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        residents = residents.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(student_id__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(company_name__icontains=q) |
            Q(department__icontains=q) |
            Q(business_name__icontains=q)
        )

    # Occupation filter
    occ = request.GET.get('occupation', '').strip()
    if occ:
        residents = residents.filter(occupation__iexact=occ)

    # Hostel filter
    hostel_id = request.GET.get('hostel', '').strip()
    if hostel_id:
        residents = residents.filter(
            allocations__bed__room__floor__building_id=hostel_id,
            allocations__status='active'
        )

    # Status filter
    status = request.GET.get('status', '').strip()
    if status:
        residents = residents.filter(status=status)

    total_count = residents.count()
    hostels = Building.objects.all()

    context = {
        'residents': residents,
        'total_count': total_count,
        'hostels': hostels,
        'selected_occ': occ,
        'selected_hostel': hostel_id,
        'selected_status': status,
        'search_query': q,
    }
    return render(request, 'admin/residents/list.html', context)


# ============================================================
# LEAVE REQUEST MANAGEMENT
# ============================================================

@admin_required
def leave_admin_list(request):
    """
    Admin view of all resident leave requests with approval actions.
    """
    leaves = LeaveRequest.objects.select_related(
        'student', 'student__user', 'action_by'
    ).all()

    status = request.GET.get('status', '').strip()
    if status:
        leaves = leaves.filter(status=status)

    q = request.GET.get('q', '').strip()
    if q:
        leaves = leaves.filter(
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q) |
            Q(student__student_id__icontains=q) |
            Q(leave_type__icontains=q) |
            Q(reason__icontains=q)
        )

    pending_count = LeaveRequest.objects.filter(status='pending').count()
    approved_count = LeaveRequest.objects.filter(status='approved').count()
    rejected_count = LeaveRequest.objects.filter(status='rejected').count()

    context = {
        'leaves': leaves,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'selected_status': status,
        'search_query': q,
    }
    return render(request, 'admin/leaves/list.html', context)


@admin_required
def leave_action(request, pk):
    """
    Approve or reject a leave request.
    """
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '').strip()
        
        if action == 'approve':
            leave.status = 'approved'
            leave.action_by = request.user
            leave.action_remarks = remarks
            leave.save()
            messages.success(request, f"Leave request for {leave.student.full_name} has been APPROVED.")
        elif action == 'reject':
            leave.status = 'rejected'
            leave.action_by = request.user
            leave.action_remarks = remarks
            leave.save()
            messages.warning(request, f"Leave request for {leave.student.full_name} has been REJECTED.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard:admin_leaves'))


# ============================================================
# NOTICES & ANNOUNCEMENTS MANAGEMENT
# ============================================================

@admin_required
def notice_admin_list(request):
    """
    Admin notice board management.
    """
    notices = Notice.objects.select_related('target_hostel', 'created_by').all()
    hostels = Building.objects.all()

    context = {
        'notices': notices,
        'total_notices': notices.count(),
        'hostels': hostels,
    }
    return render(request, 'admin/notices/list.html', context)


@admin_required
def notice_create(request):
    """
    Create a new Notice / Announcement.
    """
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, f"Notice '{notice.title}' published successfully.")
            return redirect('dashboard:admin_notices')
    else:
        form = NoticeForm()

    return render(request, 'admin/notices/form.html', {
        'form': form,
        'title': 'Publish New Notice',
        'action_label': 'Publish Notice',
    })


@admin_required
def notice_edit(request, pk):
    """
    Edit existing notice.
    """
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, f"Notice '{notice.title}' updated successfully.")
            return redirect('dashboard:admin_notices')
    else:
        form = NoticeForm(instance=notice)

    return render(request, 'admin/notices/form.html', {
        'form': form,
        'notice': notice,
        'title': f"Edit Notice: {notice.title}",
        'action_label': 'Update Notice',
    })


@admin_required
def notice_delete(request, pk):
    """
    Delete a notice.
    """
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        title = notice.title
        notice.delete()
        messages.success(request, f"Notice '{title}' deleted.")
    return redirect('dashboard:admin_notices')


# ============================================================
# SYSTEM SETTINGS & ADMIN PROFILE
# ============================================================

@admin_required
def admin_settings(request):
    """
    System overview and settings control panel.
    """
    from hostel_management import settings
    return render(request, 'admin/settings.html', {
        'app_name': 'HostelMS Enterprise',
        'version': '2.4.0',
        'server_time': timezone.now(),
        'debug_mode': settings.DEBUG,
    })
