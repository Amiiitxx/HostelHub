from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Student
from .forms import StudentForm


# ============================================================
# STAFF REQUIRED
# ============================================================

def staff_required(view_func):
    """
    Only Admin and Warden can access staff-only views.
    """

    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # Not logged in
        if not request.user.is_authenticated:

            from django.conf import settings

            return redirect(
                settings.LOGIN_URL
            )

        # Admin / Warden check
        if not request.user.can_manage_hostel:

            messages.error(
                request,
                "You don't have permission to perform this action."
            )

            return redirect(
                'dashboard:index'
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# STUDENT LIST
# ============================================================

@login_required
def student_list(request):

    # ========================================================
    # BASE QUERYSET
    # ========================================================

    base_qs = Student.objects.all()

    # --------------------------------------------------------
    # STUDENT ROLE
    # Students can see only their own profile
    # --------------------------------------------------------

    if request.user.is_student_role:

        try:

            base_qs = base_qs.filter(
                pk=request.user.student_profile.pk
            )

        except Student.DoesNotExist:

            base_qs = Student.objects.none()

    # ========================================================
    # STATISTICS
    # ========================================================

    total_students = base_qs.count()

    active_students = base_qs.filter(
        status='active'
    ).count()

    inactive_students = base_qs.filter(
        status='inactive'
    ).count()

    graduated_students = base_qs.filter(
        status='graduated'
    ).count()

    # ========================================================
    # SEARCH
    # ========================================================

    qs = base_qs

    q = request.GET.get(
        'q',
        ''
    ).strip()

    if q:

        qs = qs.filter(

            Q(first_name__icontains=q)

            | Q(last_name__icontains=q)

            | Q(student_id__icontains=q)

            | Q(email__icontains=q)

            | Q(course__icontains=q)

            | Q(phone__icontains=q)

        )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    status = request.GET.get(
        'status',
        ''
    ).strip()

    if status:

        qs = qs.filter(
            status=status
        )

    # ========================================================
    # COURSE FILTER
    # ========================================================

    course = request.GET.get(
        'course',
        ''
    ).strip()

    if course:

        qs = qs.filter(
            course__icontains=course
        )

    # ========================================================
    # OCCUPATION FILTER
    # ========================================================

    occupation = request.GET.get(
        'occupation',
        ''
    ).strip()

    if occupation:

        qs = qs.filter(
            occupation=occupation
        )

    # ========================================================
    # PAGINATION
    # ========================================================

    paginator = Paginator(
        qs.order_by('-created_at'),
        20
    )

    page = paginator.get_page(
        request.GET.get(
            'page',
            1
        )
    )

    # ========================================================
    # COURSE LIST
    # ========================================================

    courses = (
        base_qs
        .exclude(course='')
        .values_list(
            'course',
            flat=True
        )
        .distinct()
        .order_by('course')
    )

    # ========================================================
    # OCCUPATION LIST
    # ========================================================

    occupations = (
        base_qs
        .exclude(occupation='')
        .values_list(
            'occupation',
            flat=True
        )
        .distinct()
        .order_by('occupation')
    )

    # ========================================================
    # FINAL CONTEXT
    # ========================================================

    context = {

        # ----------------------------------------------------
        # STUDENTS
        # ----------------------------------------------------

        'students': page,

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        'q': q,

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        'status_filter': status,

        'course_filter': course,

        'occupation_filter': occupation,

        # ----------------------------------------------------
        # FILTER OPTIONS
        # ----------------------------------------------------

        'courses': courses,

        'occupations': occupations,

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        'total': total_students,

        'total_students': total_students,

        'active_students': active_students,

        'inactive_students': inactive_students,

        'graduated_students': graduated_students,

    }

    return render(
        request,
        'students/list.html',
        context
    )


# ============================================================
# STUDENT DETAIL
# ============================================================

@login_required
def student_detail(request, pk):

    student = get_object_or_404(
        Student,
        pk=pk
    )

    # ========================================================
    # ROLE RESTRICTION
    # ========================================================

    if request.user.is_student_role:

        try:

            if request.user.student_profile.pk != student.pk:

                messages.error(
                    request,
                    "Access denied."
                )

                return redirect(
                    'dashboard:index'
                )

        except Student.DoesNotExist:

            messages.error(
                request,
                "Access denied."
            )

            return redirect(
                'dashboard:index'
            )

    # ========================================================
    # RELATED DATA
    # ========================================================

    from fees.models import Fee
    from complaints.models import Complaint
    from attendance.models import Attendance

    # --------------------------------------------------------
    # Fees
    # --------------------------------------------------------

    fees = Fee.objects.filter(
        student=student
    ).order_by(
        '-created_at'
    )

    # --------------------------------------------------------
    # Complaints
    # --------------------------------------------------------

    complaints = Complaint.objects.filter(
        student=student
    ).order_by(
        '-created_at'
    )

    # --------------------------------------------------------
    # Attendance
    # --------------------------------------------------------

    attendance_records = Attendance.objects.filter(
        student=student
    ).order_by(
        '-date'
    )[:30]

    # --------------------------------------------------------
    # Allocation
    # --------------------------------------------------------

    allocation = student.get_current_allocation()

    # --------------------------------------------------------
    # Attendance Percentage
    # --------------------------------------------------------

    attendance_pct = student.get_attendance_percentage()

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        'student': student,

        'fees': fees,

        'complaints': complaints,

        'attendance_records': attendance_records,

        'allocation': allocation,

        'attendance_pct': attendance_pct,

    }

    return render(
        request,
        'students/detail.html',
        context
    )


# ============================================================
# CREATE STUDENT
# ============================================================

@staff_required
def student_create(request):

    if request.method == 'POST':

        form = StudentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            student = form.save()

            messages.success(
                request,
                f"Student {student.full_name} created successfully."
            )

            return redirect(
                'students:detail',
                pk=student.pk
            )

    else:

        form = StudentForm()

    return render(
        request,
        'students/form.html',
        {
            'form': form,
            'title': 'Add Student',
            'action': 'Create'
        }
    )


# ============================================================
# EDIT STUDENT
# ============================================================

@staff_required
def student_edit(request, pk):

    student = get_object_or_404(
        Student,
        pk=pk
    )

    if request.method == 'POST':

        form = StudentForm(
            request.POST,
            request.FILES,
            instance=student
        )

        if form.is_valid():

            student = form.save()

            messages.success(
                request,
                f"Student {student.full_name} updated successfully."
            )

            return redirect(
                'students:detail',
                pk=student.pk
            )

    else:

        form = StudentForm(
            instance=student
        )

    return render(
        request,
        'students/form.html',
        {
            'form': form,
            'title': 'Edit Student',
            'student': student,
            'action': 'Update'
        }
    )


# ============================================================
# DELETE STUDENT
# ============================================================

@staff_required
def student_delete(request, pk):

    student = get_object_or_404(
        Student,
        pk=pk
    )

    if request.method == 'POST':

        name = student.full_name

        student.delete()

        messages.success(
            request,
            f"Student {name} deleted."
        )

        return redirect(
            'students:list'
        )

    return render(
        request,
        'students/confirm_delete.html',
        {
            'student': student
        }
    )