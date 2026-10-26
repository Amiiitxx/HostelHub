from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from functools import wraps

from .models import Visitor
from students.models import Student


# =========================================================
# STAFF REQUIRED
# =========================================================

def staff_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)

        if not request.user.can_manage_hostel:
            messages.error(
                request,
                "Access denied. Staff access required."
            )
            return redirect('dashboard:index')

        return view_func(request, *args, **kwargs)

    return wrapper


# =========================================================
# VISITOR LIST
# =========================================================

@login_required
def visitor_list(request):

    # STUDENT
    if request.user.is_student_role:

        try:
            student = request.user.student_profile

            qs = Visitor.objects.select_related(
                'student'
            ).filter(
                student=student,
                status__in=[
                    'pending',
                    'rejected'
                ]
            )

        except Exception:
            qs = Visitor.objects.none()

        q = request.GET.get('q', '').strip()

        if q:
            qs = qs.filter(
                Q(visitor_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(purpose__icontains=q)
            )

        paginator = Paginator(
            qs.order_by('-created_at'),
            10
        )

        page = paginator.get_page(
            request.GET.get('page', 1)
        )

        return render(
            request,
            'visitors/student_list.html',
            {
                'visitors': page,
                'q': q,
            }
        )

    # ADMIN / WARDEN

    qs = Visitor.objects.select_related(
        'student',
        'registered_by',
        'approved_by'
    )

    q = request.GET.get('q', '').strip()

    if q:
        qs = qs.filter(
            Q(visitor_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(student__first_name__icontains=q)
            | Q(student__last_name__icontains=q)
        )

    status_filter = request.GET.get(
        'status',
        ''
    )

    if status_filter:
        qs = qs.filter(
            status=status_filter
        )

    date_filter = request.GET.get(
        'date',
        ''
    )

    if date_filter:
        qs = qs.filter(
            visit_date=date_filter
        )

    today = timezone.localdate()

    total_count = Visitor.objects.count()

    pending_count = Visitor.objects.filter(
        status='pending'
    ).count()

    approved_count = Visitor.objects.filter(
        status='approved'
    ).count()

    inside_count = Visitor.objects.filter(
        status='inside'
    ).count()

    rejected_count = Visitor.objects.filter(
        status='rejected'
    ).count()

    completed_count = Visitor.objects.filter(
        status='completed'
    ).count()

    today_count = Visitor.objects.filter(
        visit_date=today
    ).count()

    paginator = Paginator(
        qs.order_by('-created_at'),
        20
    )

    page = paginator.get_page(
        request.GET.get('page', 1)
    )

    return render(
        request,
        'visitors/list.html',
        {
            'visitors': page,
            'q': q,
            'status_filter': status_filter,
            'date_filter': date_filter,
            'total_count': total_count,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'inside_count': inside_count,
            'rejected_count': rejected_count,
            'completed_count': completed_count,
            'today_count': today_count,
            'today': today,
            'statuses': Visitor.STATUS_CHOICES,
        }
    )


# =========================================================
# STUDENT APPLY
# =========================================================

@login_required
def visitor_apply(request):

    # Staff should not use student request form
    if request.user.can_manage_hostel:
        return redirect('visitors:list')

    if not request.user.is_student_role:
        messages.error(
            request,
            "Only students can apply for visitors."
        )
        return redirect('dashboard:index')

    try:
        student = request.user.student_profile
    except Exception:
        messages.error(
            request,
            "Student profile not found."
        )
        return redirect('dashboard:index')

    if request.method == 'POST':

        visitor_name = request.POST.get(
            'visitor_name',
            ''
        ).strip()

        phone = request.POST.get(
            'phone',
            ''
        ).strip()

        relation = request.POST.get(
            'relation',
            ''
        ).strip()

        purpose = request.POST.get(
            'purpose',
            ''
        ).strip()

        visit_date = request.POST.get(
            'visit_date',
            ''
        )

        expected_arrival = request.POST.get(
            'expected_arrival',
            ''
        )

        expected_departure = request.POST.get(
            'expected_departure',
            ''
        )

        id_proof = request.POST.get(
            'id_proof',
            ''
        ).strip()

        notes = request.POST.get(
            'notes',
            ''
        ).strip()

        if not visitor_name:
            messages.error(
                request,
                "Visitor name is required."
            )

            return render(
                request,
                'visitors/form.html',
                {'visitor': request.POST}
            )

        if not phone:
            messages.error(
                request,
                "Phone number is required."
            )

            return render(
                request,
                'visitors/form.html',
                {'visitor': request.POST}
            )

        if not visit_date:
            messages.error(
                request,
                "Visit date is required."
            )

            return render(
                request,
                'visitors/form.html',
                {'visitor': request.POST}
            )

        try:

            Visitor.objects.create(
                student=student,
                visitor_name=visitor_name,
                phone=phone,
                relation=relation,
                purpose=purpose,
                visit_date=visit_date,
                expected_arrival=expected_arrival or None,
                expected_departure=expected_departure or None,
                id_proof=id_proof,
                notes=notes,
                status='pending',
                check_in=None,
                check_out=None,
                registered_by=request.user,
            )

            messages.success(
                request,
                "Visitor request submitted successfully. "
                "It is now pending approval."
            )

            return redirect(
                'visitors:list'
            )

        except Exception as e:

            messages.error(
                request,
                f"Unable to submit request: {e}"
            )

    return render(
        request,
        'visitors/form.html'
    )


# =========================================================
# ADMIN DIRECT CHECK-IN
# =========================================================

@staff_required
def visitor_create(request):

    students = Student.objects.filter(
        status='active'
    ).order_by('first_name')

    if request.method == 'POST':

        student_id = request.POST.get(
            'student'
        )

        visitor_name = request.POST.get(
            'visitor_name'
        )

        phone = request.POST.get(
            'phone'
        )

        relation = request.POST.get(
            'relation',
            ''
        )

        purpose = request.POST.get(
            'purpose',
            ''
        )

        visit_date = request.POST.get(
            'visit_date'
        )

        expected_arrival = request.POST.get(
            'expected_arrival'
        )

        expected_departure = request.POST.get(
            'expected_departure'
        )

        id_proof = request.POST.get(
            'id_proof',
            ''
        )

        try:

            Visitor.objects.create(
                student_id=student_id,
                visitor_name=visitor_name,
                phone=phone,
                relation=relation,
                purpose=purpose,
                visit_date=visit_date or timezone.localdate(),
                expected_arrival=expected_arrival or None,
                expected_departure=expected_departure or None,
                id_proof=id_proof,
                registered_by=request.user,
                status='inside',
                check_in=timezone.now(),
                check_out=None,
            )

            messages.success(
                request,
                f"{visitor_name} checked in successfully."
            )

            return redirect(
                'visitors:list'
            )

        except Exception as e:

            messages.error(
                request,
                f"Error: {e}"
            )

    return render(
        request,
        'visitors/admin_form.html',
        {
            'students': students
        }
    )


# =========================================================
# APPROVE
# =========================================================

@staff_required
def visitor_approve(request, pk):

    visitor = get_object_or_404(
        Visitor,
        pk=pk
    )

    if request.method == 'POST':

        if visitor.status != 'pending':
            messages.warning(
                request,
                "Only pending requests can be approved."
            )
            return redirect('visitors:list')

        visitor.status = 'approved'
        visitor.approved_by = request.user
        visitor.approved_at = timezone.now()
        visitor.rejected_reason = ''

        visitor.save(
            update_fields=[
                'status',
                'approved_by',
                'approved_at',
                'rejected_reason'
            ]
        )

        messages.success(
            request,
            f"{visitor.visitor_name} has been approved."
        )

    return redirect('visitors:list')


# =========================================================
# REJECT
# =========================================================

@staff_required
def visitor_reject(request, pk):

    visitor = get_object_or_404(
        Visitor,
        pk=pk
    )

    if request.method == 'POST':

        if visitor.status != 'pending':
            messages.warning(
                request,
                "Only pending requests can be rejected."
            )
            return redirect('visitors:list')

        reason = request.POST.get(
            'reason',
            ''
        ).strip()

        visitor.status = 'rejected'
        visitor.rejected_reason = reason
        visitor.approved_by = request.user
        visitor.approved_at = timezone.now()

        visitor.save(
            update_fields=[
                'status',
                'rejected_reason',
                'approved_by',
                'approved_at'
            ]
        )

        messages.success(
            request,
            f"{visitor.visitor_name} has been rejected."
        )

    return redirect('visitors:list')


# =========================================================
# CHECK IN
# =========================================================

@staff_required
def visitor_checkin(request, pk):

    visitor = get_object_or_404(
        Visitor,
        pk=pk
    )

    if request.method == 'POST':

        if visitor.status != 'approved':
            messages.warning(
                request,
                "Only approved visitors can be checked in."
            )
            return redirect('visitors:list')

        visitor.status = 'inside'
        visitor.check_in = timezone.now()
        visitor.check_out = None

        visitor.save(
            update_fields=[
                'status',
                'check_in',
                'check_out'
            ]
        )

        messages.success(
            request,
            f"{visitor.visitor_name} checked in successfully."
        )

    return redirect('visitors:list')


# =========================================================
# CHECK OUT
# =========================================================

@staff_required
def visitor_checkout(request, pk):

    visitor = get_object_or_404(
        Visitor,
        pk=pk
    )

    if request.method == 'POST':

        if visitor.status != 'inside':
            messages.warning(
                request,
                "Visitor is not currently inside."
            )
            return redirect('visitors:list')

        visitor.do_checkout()

        messages.success(
            request,
            f"{visitor.visitor_name} checked out successfully."
        )

    return redirect('visitors:list')