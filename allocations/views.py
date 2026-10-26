from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Allocation
from students.models import Student
from hostel.models import Building, Bed


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
def allocation_list(request):
    qs = Allocation.objects.select_related('student', 'bed__room__floor__building')
    if request.user.is_student_role:
        try:
            qs = qs.filter(student=request.user.student_profile)
        except Student.DoesNotExist:
            qs = Allocation.objects.none()

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) |
            Q(student__student_id__icontains=q) | Q(bed__room__room_number__icontains=q)
        )

    paginator = Paginator(qs.order_by('-created_at'), 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'allocations/list.html', {
        'allocations': page,
        'q': q,
        'status_filter': status,
        'total': qs.count(),
    })


@staff_required
def allocation_create(request):
    buildings = Building.objects.prefetch_related('floors').all()
    students_unallocated = Student.objects.filter(status='active').exclude(
        allocations__status='active'
    )
    preselect_student = request.GET.get('student')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        bed_id = request.POST.get('bed')
        allocated_date = request.POST.get('allocated_date')
        notes = request.POST.get('notes', '')

        try:
            student = get_object_or_404(Student, pk=student_id)
            bed = get_object_or_404(Bed, pk=bed_id)
            alloc = Allocation(
                student=student,
                bed=bed,
                allocated_date=allocated_date,
                notes=notes,
                allocated_by=request.user,
                status='active',
            )
            alloc.full_clean()
            alloc.save()
            messages.success(request, f"Bed allocated to {student.full_name} successfully.")
            return redirect('allocations:list')
        except Exception as e:
            messages.error(request, f"Allocation failed: {e}")

    return render(request, 'allocations/create.html', {
        'buildings': buildings,
        'students': students_unallocated,
        'preselect_student': preselect_student,
    })


@staff_required
def allocation_vacate(request, pk):
    allocation = get_object_or_404(Allocation, pk=pk)
    if request.method == 'POST':
        allocation.vacate(user=request.user)
        messages.success(request, f"Bed vacated for {allocation.student.full_name}.")
    next_url = request.POST.get('next') or request.GET.get('next') or 'allocations:list'
    return redirect(next_url)


@login_required
def allocation_detail(request, pk):
    alloc = get_object_or_404(Allocation.objects.select_related('student', 'bed__room__floor__building'), pk=pk)
    return render(request, 'allocations/detail.html', {'alloc': alloc})
