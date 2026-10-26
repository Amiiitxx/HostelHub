from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from .models import Attendance
from students.models import Student
import json


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
def index(request):
    today = timezone.now().date()
    selected_date = request.GET.get('date', str(today))

    try:
        from datetime import date
        sel_date = date.fromisoformat(selected_date)
    except Exception:
        sel_date = today
        selected_date = str(today)

    students = Student.objects.filter(status='active').order_by('first_name', 'last_name')

    # Get existing attendance for selected date
    existing = {
        att.student_id: att
        for att in Attendance.objects.filter(date=sel_date)
    }

    student_attendance = []
    for s in students:
        att = existing.get(s.pk)
        student_attendance.append({
            'student': s,
            'attendance': att,
            'status': att.status if att else '',
        })

    present_count = sum(1 for sa in student_attendance if sa['status'] == 'present')
    absent_count = sum(1 for sa in student_attendance if sa['status'] == 'absent')
    not_marked = sum(1 for sa in student_attendance if not sa['status'])

    # Monthly summary for chart
    month_data = []
    for day in range(1, sel_date.day + 1):
        d = sel_date.replace(day=day)
        p = Attendance.objects.filter(date=d, status='present').count()
        a = Attendance.objects.filter(date=d, status='absent').count()
        month_data.append({'day': day, 'present': p, 'absent': a})

    return render(request, 'attendance/index.html', {
        'student_attendance': student_attendance,
        'selected_date': selected_date,
        'sel_date': sel_date,
        'present_count': present_count,
        'absent_count': absent_count,
        'not_marked': not_marked,
        'total_students': students.count(),
        'month_data': month_data,
    })


@staff_required
def bulk_save(request):
    """AJAX endpoint: save bulk attendance"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            att_date = data.get('date')
            records = data.get('records', [])

            from datetime import date
            att_date = date.fromisoformat(att_date)

            saved = 0
            for rec in records:
                student_id = rec.get('student_id')
                status = rec.get('status')
                if not status:
                    continue
                Attendance.objects.update_or_create(
                    student_id=student_id,
                    date=att_date,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                    }
                )
                saved += 1

            return JsonResponse({'success': True, 'saved': saved})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def student_attendance(request, student_pk):
    from students.models import Student as StudentModel
    from django.shortcuts import get_object_or_404
    student = get_object_or_404(StudentModel, pk=student_pk)
    if request.user.is_student_role:
        try:
            if request.user.student_profile != student:
                messages.error(request, "Access denied.")
                return redirect('dashboard:index')
        except Exception:
            return redirect('dashboard:index')

    records = Attendance.objects.filter(student=student).order_by('-date')
    total = records.count()
    present = records.filter(status='present').count()
    pct = round((present / total * 100), 1) if total else 0
    return render(request, 'attendance/student.html', {
        'student': student,
        'records': records[:60],
        'total': total,
        'present': present,
        'absent': total - present,
        'pct': pct,
    })
