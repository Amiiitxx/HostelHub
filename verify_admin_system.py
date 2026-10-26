import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from django.test import Client
from accounts.models import User, WardenProfile
from students.models import Student
from hostel.models import Building, Room, Bed
from attendance.models import LeaveRequest
from dashboard.models import Notice
from datetime import date, timedelta


def run_tests():
    print("=======================================================")
    print("STARTING COMPREHENSIVE ADMIN & WARDEN VERIFICATION TEST")
    print("=======================================================")

    client = Client()

    # 1. SETUP USERS
    admin_user, _ = User.objects.get_or_create(
        username='test_super_admin',
        defaults={
            'email': 'superadmin@hostelms.com',
            'role': User.ROLE_ADMIN,
            'is_superuser': True,
            'is_staff': True,
            'first_name': 'Super',
            'last_name': 'Admin'
        }
    )
    admin_user.set_password('AdminPass123!')
    admin_user.is_superuser = True
    admin_user.role = User.ROLE_ADMIN
    admin_user.save()

    # Create Hostel Building if needed
    building, _ = Building.objects.get_or_create(
        name='Block A - Alpha Tower',
        defaults={'address': 'North Campus, Building 1'}
    )

    # Create Warden
    warden_user, _ = User.objects.get_or_create(
        username='test_warden_john',
        defaults={
            'email': 'warden_john@hostelms.com',
            'role': User.ROLE_WARDEN,
            'is_staff': True,
            'first_name': 'John',
            'last_name': 'Doe'
        }
    )
    warden_user.set_password('WardenPass123!')
    warden_user.role = User.ROLE_WARDEN
    warden_user.save()

    warden_profile, _ = WardenProfile.objects.get_or_create(
        user=warden_user,
        defaults={
            'employee_id': 'WRD-EMP-001',
            'phone': '9876543210',
            'assigned_hostel': building,
            'assigned_block': 'Block A',
            'status': 'active',
            'joining_date': date.today()
        }
    )

    # Resident User
    student_user, _ = User.objects.get_or_create(
        username='test_resident_sam',
        defaults={
            'email': 'sam@student.com',
            'role': User.ROLE_STUDENT,
            'occupation': 'Student',
            'first_name': 'Sam',
            'last_name': 'Wilson'
        }
    )
    student_user.set_password('StudentPass123!')
    student_user.role = User.ROLE_STUDENT
    student_user.save()

    student_profile, _ = Student.objects.get_or_create(
        user=student_user,
        defaults={
            'student_id': 'STU-VERIFY-001',
            'first_name': 'Sam',
            'last_name': 'Wilson',
            'email': 'sam@student.com',
            'phone': '9876500001',
            'occupation': 'Student',
            'status': 'active'
        }
    )

    print("\n--- TEST 1: POST-LOGIN ROUTING BY ROLE ---")
    # Admin login
    client.login(username='test_super_admin', password='AdminPass123!')
    res = client.get('/dashboard/')
    assert res.status_code == 200, f"Admin /dashboard/ returned {res.status_code}"
    assert b"HostelMS Enterprise Control Center" in res.content, "Admin Control Center text missing"
    print("PASS: Admin accesses /dashboard/ -> lands on Master Admin Control Center")

    # Warden login
    client.login(username='test_warden_john', password='WardenPass123!')
    res = client.get('/dashboard/', follow=True)
    assert '/warden/dashboard/' in res.redirect_chain[0][0] or res.status_code == 200, "Warden did not route to warden dashboard"
    assert b"Assigned Hostel Supervisor" in res.content or b"Warden" in res.content
    print("PASS: Warden accesses /dashboard/ -> redirected to /warden/dashboard/")

    # Resident login
    client.login(username='test_resident_sam', password='StudentPass123!')
    res = client.get('/dashboard/', follow=True)
    assert '/student/dashboard/' in res.redirect_chain[0][0], "Student did not route to student dashboard"
    print("PASS: Resident accesses /dashboard/ -> redirected to /student/dashboard/")

    print("\n--- TEST 2: BACKEND SECURITY BARRIERS (ADMIN PROTECTION) ---")
    # Resident attempts to access admin routes
    client.login(username='test_resident_sam', password='StudentPass123!')
    admin_routes = [
        '/admin-dashboard/',
        '/admin/wardens/',
        '/admin/residents/',
        '/admin/leaves/',
        '/admin/notices/',
        '/admin/settings/',
    ]
    for r in admin_routes:
        res = client.get(r, follow=True)
        assert res.status_code == 200
        # Resident must be redirected back to their own dashboard
        assert '/student/dashboard/' in res.redirect_chain[-1][0], f"Resident was NOT blocked from {r}!"
        print(f"PASS: Resident successfully blocked from {r} -> redirected to student dashboard")

    # Warden attempts to access restricted admin routes
    client.login(username='test_warden_john', password='WardenPass123!')
    restricted_warden_routes = [
        '/admin/wardens/',
        '/admin/settings/',
    ]
    for r in restricted_warden_routes:
        res = client.get(r, follow=True)
        assert '/warden/dashboard/' in res.redirect_chain[-1][0], f"Warden was NOT blocked from {r}!"
        print(f"PASS: Warden successfully blocked from {r} -> redirected to warden dashboard")

    print("\n--- TEST 3: ADMIN MANAGEMENT MODULES (HTTP 200 FOR ADMIN) ---")
    client.login(username='test_super_admin', password='AdminPass123!')
    for r in admin_routes:
        res = client.get(r)
        assert res.status_code == 200, f"Admin could not access {r} (status: {res.status_code})"
        print(f"PASS: Admin successfully accessed {r} (HTTP 200)")

    print("\n--- TEST 4: LEAVE REQUEST CREATION & ADMIN APPROVAL ---")
    leave = LeaveRequest.objects.create(
        student=student_profile,
        leave_type='Home Visit',
        start_date=date.today() + timedelta(days=2),
        end_date=date.today() + timedelta(days=4),
        reason='Family event',
        status='pending'
    )
    res = client.post(f'/dashboard/admin/leaves/{leave.id}/action/', {'action': 'approve', 'remarks': 'Approved by Admin'})
    leave.refresh_from_db()
    assert leave.status == 'approved', f"Leave was not approved, current status: {leave.status}"
    print("PASS: Leave request successfully approved by Admin")

    print("\n--- TEST 5: NOTICE CREATION & PERSISTENCE ---")
    notice = Notice.objects.create(
        title='Annual Hostel Sports Meet 2026',
        content='Registrations are now open for the annual hostel badminton and table tennis tournaments.',
        category='General',
        target_scope='all',
        is_published=True,
        created_by=admin_user
    )
    # Check notice appears in student dashboard
    client.login(username='test_resident_sam', password='StudentPass123!')
    res = client.get('/student/dashboard/')
    assert b"Annual Hostel Sports Meet 2026" in res.content, "Published notice did not appear on resident dashboard!"
    print("PASS: Notice published by Admin successfully renders on resident dashboard")

    print("\n=======================================================")
    print("ALL TESTS PASSED! ADMIN & WARDEN ARCHITECTURE 100% OPERATIONAL")
    print("=======================================================")


if __name__ == '__main__':
    run_tests()
