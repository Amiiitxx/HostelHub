from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
import csv
import io
from datetime import date, timedelta


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


def get_date_range(request):
    today = date.today()
    period = request.GET.get('period', 'month')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from and date_to:
        try:
            return date.fromisoformat(date_from), date.fromisoformat(date_to)
        except Exception:
            pass
    if period == 'today':
        return today, today
    elif period == 'week':
        return today - timedelta(days=7), today
    elif period == 'month':
        return today.replace(day=1), today
    elif period == 'year':
        return today.replace(month=1, day=1), today
    return today.replace(day=1), today


@staff_required
def index(request):
    return render(request, 'reports/index.html')


@staff_required
def occupancy_report(request):
    from hostel.models import Building, Room, Bed
    buildings = Building.objects.prefetch_related('floors__rooms__beds').all()
    total_beds = Bed.objects.count()
    occupied = Bed.objects.filter(status='occupied').count()
    available = Bed.objects.filter(status='available').count()
    maintenance = Bed.objects.filter(status='maintenance').count()
    occ_pct = round(occupied / total_beds * 100, 1) if total_beds else 0

    if request.GET.get('export') == 'csv':
        return _export_occupancy_csv(buildings)

    return render(request, 'reports/occupancy.html', {
        'buildings': buildings,
        'total_beds': total_beds,
        'occupied': occupied,
        'available': available,
        'maintenance': maintenance,
        'occ_pct': occ_pct,
    })


@staff_required
def student_report(request):
    from students.models import Student
    qs = Student.objects.all()
    status = request.GET.get('status', '')
    course = request.GET.get('course', '')
    if status:
        qs = qs.filter(status=status)
    if course:
        qs = qs.filter(course__icontains=course)
    if request.GET.get('export') == 'csv':
        return _export_students_csv(qs)
    courses = Student.objects.values_list('course', flat=True).distinct()
    return render(request, 'reports/students.html', {
        'students': qs.order_by('first_name'),
        'status_filter': status,
        'course_filter': course,
        'courses': courses,
        'total': qs.count(),
    })


@staff_required
def fee_report(request):
    from fees.models import Fee
    d_from, d_to = get_date_range(request)
    qs = Fee.objects.filter(created_at__date__gte=d_from, created_at__date__lte=d_to).select_related('student')
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    totals = qs.aggregate(total=Sum('amount'), paid=Sum('amount', filter=Q(status='paid')),
                          pending=Sum('amount', filter=Q(status='pending')),
                          overdue=Sum('amount', filter=Q(status='overdue')))
    if request.GET.get('export') == 'csv':
        return _export_fees_csv(qs)
    return render(request, 'reports/fees.html', {
        'fees': qs.order_by('-created_at'),
        'totals': totals,
        'd_from': d_from,
        'd_to': d_to,
        'status_filter': status,
        'period': request.GET.get('period', 'month'),
    })


@staff_required
def complaint_report(request):
    from complaints.models import Complaint
    d_from, d_to = get_date_range(request)
    qs = Complaint.objects.filter(created_at__date__gte=d_from, created_at__date__lte=d_to).select_related('student')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if request.GET.get('export') == 'csv':
        return _export_complaints_csv(qs)
    return render(request, 'reports/complaints.html', {
        'complaints': qs.order_by('-created_at'),
        'total': qs.count(),
        'd_from': d_from,
        'd_to': d_to,
        'status_filter': status,
        'priority_filter': priority,
        'period': request.GET.get('period', 'month'),
    })


@staff_required
def visitor_report(request):
    from visitors.models import Visitor
    d_from, d_to = get_date_range(request)
    qs = Visitor.objects.filter(check_in__date__gte=d_from, check_in__date__lte=d_to).select_related('student')
    if request.GET.get('export') == 'csv':
        return _export_visitors_csv(qs)
    return render(request, 'reports/visitors.html', {
        'visitors': qs.order_by('-check_in'),
        'total': qs.count(),
        'd_from': d_from,
        'd_to': d_to,
        'period': request.GET.get('period', 'month'),
    })


@staff_required
def attendance_report(request):
    from attendance.models import Attendance
    d_from, d_to = get_date_range(request)
    qs = Attendance.objects.filter(date__gte=d_from, date__lte=d_to).select_related('student')
    if request.GET.get('export') == 'csv':
        return _export_attendance_csv(qs)
    present = qs.filter(status='present').count()
    absent = qs.filter(status='absent').count()
    return render(request, 'reports/attendance.html', {
        'records': qs.order_by('-date'),
        'present': present,
        'absent': absent,
        'total': qs.count(),
        'd_from': d_from,
        'd_to': d_to,
        'period': request.GET.get('period', 'month'),
    })


@staff_required
def allocation_report(request):
    from allocations.models import Allocation
    qs = Allocation.objects.select_related('student', 'bed__room__floor__building').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    if request.GET.get('export') == 'csv':
        return _export_allocations_csv(qs)
    return render(request, 'reports/allocations.html', {
        'allocations': qs,
        'status_filter': status,
        'total': qs.count(),
    })


# ============================================================
# CSV Export helpers
# ============================================================

def _csv_response(filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _export_students_csv(qs):
    response = _csv_response('students_report.csv')
    w = csv.writer(response)
    w.writerow(['Student ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Course', 'Year', 'Status', 'Admission Date'])
    for s in qs:
        w.writerow([s.student_id, s.first_name, s.last_name, s.email, s.phone, s.course, s.year, s.status, s.admission_date])
    return response


def _export_fees_csv(qs):
    response = _csv_response('fees_report.csv')
    w = csv.writer(response)
    w.writerow(['Student ID', 'Student Name', 'Fee Type', 'Amount', 'Due Date', 'Status', 'Created'])
    for f in qs:
        w.writerow([f.student.student_id, f.student.full_name, f.get_fee_type_display(), f.amount, f.due_date, f.status, f.created_at.date()])
    return response


def _export_complaints_csv(qs):
    response = _csv_response('complaints_report.csv')
    w = csv.writer(response)
    w.writerow(['ID', 'Student', 'Category', 'Priority', 'Title', 'Status', 'Created', 'Resolved'])
    for c in qs:
        w.writerow([c.pk, c.student.full_name, c.category, c.priority, c.title, c.status, c.created_at.date(), c.resolved_at.date() if c.resolved_at else ''])
    return response


def _export_visitors_csv(qs):
    response = _csv_response('visitors_report.csv')
    w = csv.writer(response)
    w.writerow(['Visitor Name', 'Phone', 'Student', 'Relation', 'Check In', 'Check Out'])
    for v in qs:
        w.writerow([v.visitor_name, v.phone, v.student.full_name, v.relation, v.check_in, v.check_out or 'Still Inside'])
    return response


def _export_attendance_csv(qs):
    response = _csv_response('attendance_report.csv')
    w = csv.writer(response)
    w.writerow(['Date', 'Student ID', 'Student Name', 'Status', 'Remarks'])
    for a in qs:
        w.writerow([a.date, a.student.student_id, a.student.full_name, a.status, a.remarks])
    return response


def _export_allocations_csv(qs):
    response = _csv_response('allocations_report.csv')
    w = csv.writer(response)
    w.writerow(['Student', 'Building', 'Floor', 'Room', 'Bed', 'Allocated Date', 'Vacated Date', 'Status'])
    for a in qs:
        w.writerow([a.student.full_name, a.bed.room.floor.building.name, a.bed.room.floor.name,
                    a.bed.room.room_number, a.bed.bed_number, a.allocated_date, a.vacated_date or '', a.status])
    return response


def _export_occupancy_csv(buildings):
    response = _csv_response('occupancy_report.csv')
    w = csv.writer(response)
    w.writerow(['Building', 'Floor', 'Room', 'Type', 'Capacity', 'Occupied', 'Available', 'Status'])
    for b in buildings:
        for floor in b.floors.all():
            for room in floor.rooms.all():
                w.writerow([b.name, floor.name, room.room_number, room.room_type,
                             room.capacity, room.occupied_beds, room.available_beds, room.status])
    return response
