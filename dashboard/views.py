from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from datetime import timedelta, date

from students.models import Student
from hostel.models import Building, Room, Bed
from allocations.models import Allocation
from fees.models import Fee, Payment
from complaints.models import Complaint
from visitors.models import Visitor
from attendance.models import Attendance, LeaveRequest
from accounts.models import User, WardenProfile
from .models import Notice
from .security import (
    occupation_required,
    admin_required,
    warden_required,
    get_dashboard_url_for_user,
    get_user_occupation,
    normalize_occupation,
)


def get_user_base_context(request):
    """
    Builds the base context for resident dashboards, extracting room allocation,
    fees, complaints, attendance, and general hostel information.
    """
    profile = None
    occupation = None
    try:
        profile = Student.objects.get(user=request.user)
        occupation = profile.occupation or getattr(request.user, 'occupation', 'Other')
    except Student.DoesNotExist:
        profile = None
        occupation = getattr(request.user, 'occupation', 'Other')

    allocation = profile.get_current_allocation() if profile else None
    room = allocation.room if allocation else None
    bed = allocation.bed if allocation else None

    building_name = "Main Block"
    if room and room.floor and hasattr(room.floor, 'building') and room.floor.building:
        building_name = room.floor.building.name
    elif room and room.floor:
        building_name = f"Floor {room.floor.floor_number}"

    pending_fees = profile.get_pending_fees_total() if profile else 0
    attendance_pct = profile.get_attendance_percentage() if profile else 0

    complaints = (
        Complaint.objects.filter(student=profile).order_by('-created_at')[:5]
        if profile else []
    )
    visitors = (
        Visitor.objects.filter(student=profile).order_by('-check_in')[:5]
        if profile else []
    )
    recent_fees = (
        Fee.objects.filter(student=profile).order_by('-due_date')[:5]
        if profile else []
    )

    # Real DB notices or default notices
    db_notices = list(Notice.objects.filter(is_published=True).order_by('-created_at')[:4])
    if db_notices:
        notices = [
            {
                'title': n.title,
                'date': n.created_at.strftime('%b %d, %Y'),
                'category': n.category,
                'content': n.content,
            }
            for n in db_notices
        ]
    else:
        notices = [
            {
                'title': 'Hostel Maintenance Schedule',
                'date': 'Oct 25, 2026',
                'category': 'Facility',
                'content': 'Routine water tank and electrical maintenance scheduled for Saturday 10 AM - 1 PM.'
            },
            {
                'title': 'Mess Menu & Timings Update',
                'date': 'Oct 20, 2026',
                'category': 'Dining',
                'content': 'Updated evening dinner timings: 7:30 PM to 9:30 PM starting this Monday.'
            },
            {
                'title': 'Visitor Gate Pass Policy',
                'date': 'Oct 15, 2026',
                'category': 'Security',
                'content': 'All non-resident visitors must register at the reception desk prior to entry.'
            },
        ]

    # Real DB leaves or defaults
    db_leaves = (
        list(LeaveRequest.objects.filter(student=profile).order_by('-created_at')[:5])
        if profile else []
    )
    if db_leaves:
        leave_requests = [
            {
                'leave_type': l.leave_type,
                'start_date': l.start_date.strftime('%b %d, %Y'),
                'end_date': l.end_date.strftime('%b %d, %Y'),
                'status': l.get_status_display(),
            }
            for l in db_leaves
        ]
    else:
        leave_requests = [
            {
                'leave_type': 'Weekend Home Visit',
                'start_date': 'Oct 24, 2026',
                'end_date': 'Oct 26, 2026',
                'status': 'Approved',
            },
            {
                'leave_type': 'Personal Outstation',
                'start_date': 'Nov 02, 2026',
                'end_date': 'Nov 04, 2026',
                'status': 'Pending',
            }
        ]

    return {
        'profile': profile,
        'occupation': occupation,
        'allocation': allocation,
        'room': room,
        'bed': bed,
        'building_name': building_name,
        'pending_fees': pending_fees,
        'attendance_pct': attendance_pct,
        'complaints': complaints,
        'complaints_count': len(complaints),
        'visitors': visitors,
        'visitors_count': len(visitors),
        'recent_fees': recent_fees,
        'notices': notices,
        'leave_requests': leave_requests,
        'today': date.today(),
    }


def get_admin_dashboard_context(request):
    """
    Builds the master SaaS admin dashboard context with counts for each occupation,
    hostel room metrics, financial totals, and recent operational activity.
    """
    today = date.today()
    total_users = User.objects.count()
    total_residents = Student.objects.count()
    total_wardens = WardenProfile.objects.count()
    total_hostels = Building.objects.count()

    students_count = Student.objects.filter(occupation__iexact='Student').count()
    working_prof_count = Student.objects.filter(occupation__iexact='Working Professional').count()
    gov_emp_count = Student.objects.filter(occupation__iexact='Government Employee').count()
    priv_emp_count = Student.objects.filter(occupation__iexact='Private Employee').count()
    business_count = Student.objects.filter(
        Q(occupation__iexact='Business / Self Employed') | Q(occupation__iexact='Business')
    ).count()
    job_seeker_count = Student.objects.filter(occupation__iexact='Job Seeker').count()
    other_users_count = Student.objects.exclude(
        occupation__in=[
            'Student',
            'Working Professional',
            'Government Employee',
            'Private Employee',
            'Business / Self Employed',
            'Business',
            'Job Seeker',
        ]
    ).count()

    def calc_pct(cnt):
        return round((cnt / total_residents * 100), 1) if total_residents else 0

    occ_breakdown = [
        {'name': 'Students', 'count': students_count, 'pct': calc_pct(students_count), 'color': '#4f46e5'},
        {'name': 'Working Professionals', 'count': working_prof_count, 'pct': calc_pct(working_prof_count), 'color': '#0ea5e9'},
        {'name': 'Government Employees', 'count': gov_emp_count, 'pct': calc_pct(gov_emp_count), 'color': '#10b981'},
        {'name': 'Private Employees', 'count': priv_emp_count, 'pct': calc_pct(priv_emp_count), 'color': '#8b5cf6'},
        {'name': 'Business / Self Employed', 'count': business_count, 'pct': calc_pct(business_count), 'color': '#f59e0b'},
        {'name': 'Job Seekers', 'count': job_seeker_count, 'pct': calc_pct(job_seeker_count), 'color': '#ec4899'},
        {'name': 'Other', 'count': other_users_count, 'pct': calc_pct(other_users_count), 'color': '#64748b'},
    ]

    total_rooms = Room.objects.count()
    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(status='occupied').count()
    available_beds = Bed.objects.filter(status='available').count()
    occupancy_pct = round((occupied_beds / total_beds * 100) if total_beds else 0, 1)

    pending_fees = (
        Fee.objects.filter(status__in=['pending', 'overdue']).aggregate(total=Sum('amount'))['total']
        or 0
    )
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0

    active_complaints = Complaint.objects.filter(status__in=['pending', 'in_progress']).count()
    complaints_pending = Complaint.objects.filter(status='pending').count()
    complaints_in_progress = Complaint.objects.filter(status='in_progress').count()
    complaints_resolved = Complaint.objects.filter(status='resolved').count()

    visitors_today = Visitor.objects.filter(check_in__date=today).count()
    visitors_inside = Visitor.objects.filter(check_out__isnull=True).count()
    pending_leaves_count = LeaveRequest.objects.filter(status='pending').count()
    notifications_count = pending_leaves_count + active_complaints + visitors_inside

    # Hostels summary list
    hostels_summary = []
    for b in Building.objects.all():
        b_total_beds = Bed.objects.filter(room__floor__building=b).count()
        b_occupied_beds = Bed.objects.filter(room__floor__building=b, status='occupied').count()
        b_available_beds = Bed.objects.filter(room__floor__building=b, status='available').count()
        b_pct = round((b_occupied_beds / b_total_beds * 100) if b_total_beds else 0)
        wardens = [w.full_name for w in b.wardens.filter(status='active')]

        hostels_summary.append({
            'id': b.id,
            'name': b.name,
            'address': b.address,
            'total_rooms': Room.objects.filter(floor__building=b).count(),
            'total_beds': b_total_beds,
            'occupied_beds': b_occupied_beds,
            'available_beds': b_available_beds,
            'occupancy_pct': b_pct,
            'wardens': ", ".join(wardens) if wardens else "Unassigned",
        })

    recent_allocations = (
        Allocation.objects.select_related('student', 'bed__room__floor__building')
        .filter(status='active')
        .order_by('-created_at')[:5]
    )
    recent_complaints = Complaint.objects.select_related('student').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('fee__student').order_by('-paid_at')[:5]
    pending_leaves = LeaveRequest.objects.filter(status='pending').select_related('student')[:5]
    recent_notices = Notice.objects.select_related('created_by').order_by('-created_at')[:4]
    active_visitors = Visitor.objects.filter(check_out__isnull=True).select_related('student')[:5]

    return {
        'total_users': total_users,
        'total_residents': total_residents,
        'total_wardens': total_wardens,
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'occupancy_pct': occupancy_pct,
        'pending_fees': pending_fees,
        'total_revenue': total_revenue,
        'active_complaints': active_complaints,
        'complaints_pending': complaints_pending,
        'complaints_in_progress': complaints_in_progress,
        'complaints_resolved': complaints_resolved,
        'visitors_today': visitors_today,
        'visitors_inside': visitors_inside,
        'pending_leaves_count': pending_leaves_count,
        'notifications_count': notifications_count,
        'occ_breakdown': occ_breakdown,
        'hostels_summary': hostels_summary,
        'recent_allocations': recent_allocations,
        'recent_complaints': recent_complaints,
        'recent_payments': recent_payments,
        'pending_leaves': pending_leaves,
        'recent_notices': recent_notices,
        'active_visitors': active_visitors,
        'today': today,
    }


# ============================================================
# MAIN ENTRY POINT / DISPATCHER
# ============================================================

@login_required
def index(request):
    """
    Main /dashboard/ route.
    If admin: renders the Master Admin Dashboard.
    If warden: redirects to the Warden Dashboard.
    If regular resident: redirects to their respective occupation dashboard.
    """
    if (
        getattr(request.user, 'is_admin', False)
        or getattr(request.user, 'is_superuser', False)
        or (getattr(request.user, 'role', '') == 'admin')
    ):
        return admin_dashboard(request)

    if getattr(request.user, 'is_warden', False) or (getattr(request.user, 'role', '') == 'warden'):
        return redirect('dashboard:warden_dashboard')

    return redirect(get_dashboard_url_for_user(request.user))


# ============================================================
# ADMIN MASTER DASHBOARD
# ============================================================

@admin_required
def admin_dashboard(request):
    """
    Master Admin Dashboard: Premium modern SaaS control center
    with comprehensive statistics, occupation analytics, hostels matrix,
    operations feed, and shortcuts.
    """
    context = get_admin_dashboard_context(request)
    return render(request, 'admin/dashboard.html', context)


# ============================================================
# WARDEN DEDICATED DASHBOARD
# ============================================================

@warden_required
def warden_dashboard(request):
    """
    Dedicated Warden Dashboard scoped strictly to the logged-in warden's
    assigned hostel/block.
    """
    warden_profile = getattr(request.user, 'warden_profile', None)
    assigned_hostel = warden_profile.assigned_hostel if warden_profile else None

    if assigned_hostel:
        rooms = Room.objects.filter(floor__building=assigned_hostel)
        beds = Bed.objects.filter(room__floor__building=assigned_hostel)
        residents = Student.objects.filter(
            allocations__bed__room__floor__building=assigned_hostel,
            allocations__status='active'
        ).distinct()
        complaints = Complaint.objects.filter(student__in=residents).order_by('-created_at')[:6]
        active_visitors = Visitor.objects.filter(student__in=residents, check_out__isnull=True)[:6]
        pending_leaves = LeaveRequest.objects.filter(student__in=residents, status='pending')[:6]
    else:
        # Fallback if unassigned
        assigned_hostel = Building.objects.first()
        rooms = Room.objects.filter(floor__building=assigned_hostel) if assigned_hostel else Room.objects.none()
        beds = Bed.objects.filter(room__floor__building=assigned_hostel) if assigned_hostel else Bed.objects.none()
        residents = Student.objects.all()[:10]
        complaints = Complaint.objects.all().order_by('-created_at')[:6]
        active_visitors = Visitor.objects.filter(check_out__isnull=True)[:6]
        pending_leaves = LeaveRequest.objects.filter(status='pending')[:6]

    total_beds = beds.count()
    occupied_beds = beds.filter(status='occupied').count()
    available_beds = beds.filter(status='available').count()
    occupancy_pct = round((occupied_beds / total_beds * 100) if total_beds else 0, 1)

    notices = Notice.objects.filter(
        Q(target_scope='all') |
        Q(target_scope='hostel', target_hostel=assigned_hostel)
    ).order_by('-created_at')[:4]

    context = {
        'warden_profile': warden_profile,
        'assigned_hostel': assigned_hostel,
        'total_rooms': rooms.count(),
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'occupancy_pct': occupancy_pct,
        'residents_count': residents.count(),
        'residents': residents[:8],
        'complaints': complaints,
        'active_visitors': active_visitors,
        'pending_leaves': pending_leaves,
        'notices': notices,
    }
    return render(request, 'warden/dashboard.html', context)



# ============================================================
# 1. STUDENT DASHBOARD
# ============================================================

@occupation_required('student')
def student_dashboard(request):
    """
    Dedicated Student Dashboard:
    Academic details, attendance, room allocation, fees, complaints, leave requests.
    """
    context = get_user_base_context(request)
    return render(request, 'dashboard/student.html', context)


# ============================================================
# 2. WORKING PROFESSIONAL DASHBOARD
# ============================================================

@occupation_required('working_professional')
def working_professional_dashboard(request):
    """
    Dedicated Working Professional Dashboard:
    Company, designation, work location, room allocation, fees, complaints, professional profile.
    """
    context = get_user_base_context(request)
    return render(request, 'dashboard/working_professional.html', context)


# ============================================================
# 3. GOVERNMENT EMPLOYEE DASHBOARD
# ============================================================

@occupation_required('government_employee')
def government_employee_dashboard(request):
    """
    Dedicated Government Employee Dashboard:
    Department, government office, office location, room allocation, fees, complaints.
    """
    context = get_user_base_context(request)
    return render(request, 'dashboard/government_employee.html', context)


# ============================================================
# 4. PRIVATE EMPLOYEE DASHBOARD
# ============================================================

@occupation_required('private_employee')
def private_employee_dashboard(request):
    """
    Dedicated Private Employee Dashboard:
    Company, designation, work location, room allocation, fees, complaints, profile.
    Explicitly displays dynamic Occupation: PRIVATE EMPLOYEE from database.
    """
    context = get_user_base_context(request)
    return render(request, 'dashboard/private_employee.html', context)


# ============================================================
# 5. BUSINESS / SELF EMPLOYED DASHBOARD
# ============================================================

@occupation_required('business')
def business_dashboard(request):
    """
    Dedicated Business / Self Employed Dashboard:
    Business name, type, location, room allocation, fees, complaints, business profile.
    """
    context = get_user_base_context(request)
    return render(request, 'dashboard/business.html', context)


# ============================================================
# 6. JOB SEEKER DASHBOARD
# ============================================================

@occupation_required('job_seeker')
def job_seeker_dashboard(request):
    """
    Dedicated Job Seeker Dashboard:
    Qualification, skills, experience, preferred job & location, training updates.
    """
    context = get_user_base_context(request)
    context['job_updates'] = [
        {
            'title': 'Junior / Mid Python Developer',
            'company': 'Apex Soft Technologies',
            'location': 'Bangalore / Hybrid',
            'type': 'Full Time',
            'date': '2 days ago',
        },
        {
            'title': 'Django & Web Development Specialist',
            'company': 'InnoPulse Labs',
            'location': 'Remote',
            'type': 'Full Time',
            'date': '3 days ago',
        },
        {
            'title': 'Technical Operations Associate',
            'company': 'CloudBridge Global',
            'location': 'City Centre',
            'type': 'Immediate',
            'date': '4 days ago',
        },
    ]
    return render(request, 'dashboard/job_seeker.html', context)


# ============================================================
# 7. OTHER DASHBOARD
# ============================================================

@occupation_required('other')
def other_dashboard(request):
    """
    Dedicated General / Other Dashboard:
    Personal profile, description, room allocation, fees, complaints.
    """
    context = get_user_base_context(request)
    return render(request, 'dashboard/other.html', context)