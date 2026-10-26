from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Complaint, ComplaintUpdate
from students.models import Student
from accounts.models import User


def staff_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if not request.user.can_manage_hostel:
            messages.error(request, "Access denied.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def complaint_list(request):
    qs = Complaint.objects.select_related('student', 'assigned_to')
    if request.user.is_student_role:
        try:
            qs = qs.filter(student=request.user.student_profile)
        except Exception:
            qs = Complaint.objects.none()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q))

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    priority = request.GET.get('priority', '')
    if priority:
        qs = qs.filter(priority=priority)

    category = request.GET.get('category', '')
    if category:
        qs = qs.filter(category=category)

    paginator = Paginator(qs.order_by('-created_at'), 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'complaints/list.html', {
        'complaints': page,
        'q': q,
        'status_filter': status,
        'priority_filter': priority,
        'category_filter': category,
        'statuses': Complaint.STATUSES,
        'priorities': Complaint.PRIORITIES,
        'categories': Complaint.CATEGORIES,
        'total': qs.count(),
    })


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(
        Complaint.objects.select_related('student', 'assigned_to').prefetch_related('updates__updated_by'),
        pk=pk
    )
    if request.user.is_student_role:
        try:
            if request.user.student_profile != complaint.student:
                messages.error(request, "Access denied.")
                return redirect('complaints:list')
        except Exception:
            return redirect('complaints:list')

    staff_users = User.objects.filter(role__in=['admin', 'warden'])
    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'staff_users': staff_users,
        'statuses': Complaint.STATUSES,
    })


@login_required
def complaint_create(request):
    students = Student.objects.filter(status='active')
    if request.user.is_student_role:
        try:
            students = students.filter(pk=request.user.student_profile.pk)
        except Exception:
            students = Student.objects.none()

    if request.method == 'POST':
        student_id = request.POST.get('student')
        category = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')
        title = request.POST.get('title')
        description = request.POST.get('description')
        try:
            c = Complaint.objects.create(
                student_id=student_id,
                category=category,
                priority=priority,
                title=title,
                description=description,
                status='pending',
            )
            messages.success(request, f"Complaint '{title}' submitted successfully.")
            return redirect('complaints:detail', pk=c.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'complaints/form.html', {
        'students': students,
        'categories': Complaint.CATEGORIES,
        'priorities': Complaint.PRIORITIES,
        'preselect_student': request.GET.get('student'),
    })


@staff_required
def complaint_update(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        assigned_to_id = request.POST.get('assigned_to')

        if assigned_to_id:
            complaint.assigned_to_id = assigned_to_id

        if new_status and new_status != complaint.status:
            ComplaintUpdate.objects.create(
                complaint=complaint,
                updated_by=request.user,
                status=new_status,
                comment=comment or f"Status changed to {new_status}",
            )
            complaint.status = new_status
            if new_status == 'resolved':
                from django.utils import timezone
                complaint.resolved_at = timezone.now()

        complaint.save()
        messages.success(request, "Complaint updated.")
    return redirect('complaints:detail', pk=pk)


@staff_required
def complaint_delete(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        complaint.delete()
        messages.success(request, "Complaint deleted.")
        return redirect('complaints:list')
    return redirect('complaints:list')
