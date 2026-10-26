import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')
django.setup()

from django.test import Client
from accounts.models import User
from students.models import Student
from complaints.models import Complaint
from visitors.models import Visitor

def setup_users():
    print("Setting up test users for all 7 occupations + admin...")

    # 1. Admin
    admin_user, created = User.objects.get_or_create(username='admin')
    admin_user.set_password('admin123')
    admin_user.role = User.ROLE_ADMIN
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()

    # 2. 7 Occupations
    occupations = [
        ('test_student', 'Student', 'STU-101', {'course': 'Computer Science', 'year': 2}),
        ('test_working_prof', 'Working Professional', 'EMP-201', {'company_name': 'Global Tech Inc', 'designation': 'Software Engineer', 'work_location': 'Tech Park'}),
        ('test_gov_emp', 'Government Employee', 'GOV-301', {'department': 'Revenue Dept', 'government_office': 'State Secretariat', 'designation': 'Executive Officer'}),
        ('test_priv_emp', 'Private Employee', 'PVT-401', {'company_name': 'Acme Solutions Pvt Ltd', 'designation': 'Product Specialist', 'work_location': 'Cyber City'}),
        ('test_business', 'Business / Self Employed', 'BUS-501', {'business_name': 'Apex Retail Corp', 'business_type': 'Logistics & Supply', 'business_location': 'City Market'}),
        ('test_job_seeker', 'Job Seeker', 'JOB-601', {'qualification': 'MCA Graduate', 'skills': 'Python, Django, React', 'preferred_job': 'Backend Developer', 'preferred_location': 'Bangalore'}),
        ('test_other', 'Other', 'OTH-701', {}),
    ]

    for username, occ, sid, extra in occupations:
        u, _ = User.objects.get_or_create(username=username)
        u.set_password('password123')
        u.first_name = username.replace('test_', '').title()
        u.role = User.ROLE_STUDENT
        u.occupation = occ
        u.save()

        st, _ = Student.objects.get_or_create(student_id=sid)
        st.user = u
        st.first_name = u.first_name
        st.email = f"{username}@example.com"
        st.phone = "9876543210"
        st.occupation = occ
        for k, v in extra.items():
            setattr(st, k, v)
        st.save()

        # Seed sample complaint and visitor for testing rich dashboard cards
        Complaint.objects.get_or_create(
            student=st,
            title=f"Sample maintenance request for {u.first_name}",
            defaults={'description': 'Water tap needs checking.', 'category': 'plumbing', 'status': 'pending'}
        )
        Visitor.objects.get_or_create(
            student=st,
            visitor_name=f"Visitor for {u.first_name}",
            defaults={'relation': 'Colleague / Family', 'phone': '9123456780', 'purpose': 'Personal meeting'}
        )

    print("Users setup and seed data completed successfully.")

def run_tests():
    c = Client()

    print("\n--- TEST 1: REGISTRATION FLOW & DATABASE PERSISTENCE ---")
    reg_test_user = 'new_registered_priv_emp'
    # Delete if exists from previous test run
    User.objects.filter(username=reg_test_user).delete()
    Student.objects.filter(student_id='REG-PVT-999').delete()

    reg_payload = {
        'username': reg_test_user,
        'first_name': 'Adila',
        'student_id': 'REG-PVT-999',
        'phone': '9876500000',
        'email': 'adila@example.com',
        'occupation': 'Private Employee',
        'other_occupation': '',
        'company_name': 'Nexora Enterprises',
        'designation': 'Senior System Analyst',
        'work_location': 'Tech Hub 4',
        'work_shift': '9 AM - 6 PM',
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    }
    reg_res = c.post('/accounts/signup/', reg_payload, follow=False)
    assert reg_res.status_code == 302, f"Expected 302 redirect after registration, got {reg_res.status_code}"
    
    # Verify in DB
    created_u = User.objects.get(username=reg_test_user)
    assert created_u.occupation == 'Private Employee', f"User occupation expected 'Private Employee', got {created_u.occupation}"
    created_st = Student.objects.get(user=created_u)
    assert created_st.occupation == 'Private Employee'
    assert created_st.company_name == 'Nexora Enterprises'
    assert created_st.designation == 'Senior System Analyst'
    print(f"PASS: Registration for '{reg_test_user}' succeeded. Occupation correctly saved in User and Student models.")

    # Test login for this freshly registered user
    login_res = c.post('/accounts/login/', {'username': reg_test_user, 'password': 'StrongPass123!'}, follow=False)
    assert login_res.status_code == 302
    assert login_res['Location'] == '/private-employee/dashboard/', f"Expected redirect to /private-employee/dashboard/, got {login_res['Location']}"
    print(f"PASS: Newly registered '{reg_test_user}' logged in and redirected to {login_res['Location']}")
    c.logout()

    print("\n--- TEST 2: LOGIN REDIRECTIONS FOR ALL OCCUPATIONS ---")
    login_checks = [
        ('admin', 'admin123', '/dashboard/'),
        ('test_student', 'password123', '/student/dashboard/'),
        ('test_working_prof', 'password123', '/working-professional/dashboard/'),
        ('test_gov_emp', 'password123', '/government-employee/dashboard/'),
        ('test_priv_emp', 'password123', '/private-employee/dashboard/'),
        ('test_business', 'password123', '/business/dashboard/'),
        ('test_job_seeker', 'password123', '/job-seeker/dashboard/'),
        ('test_other', 'password123', '/other/dashboard/'),
    ]

    for user, pwd, expected_url in login_checks:
        c.logout()
        res = c.post('/accounts/login/', {'username': user, 'password': pwd}, follow=False)
        assert res.status_code == 302, f"Expected 302 redirect for {user}, got {res.status_code}"
        assert res['Location'] == expected_url, f"Expected redirect to {expected_url} for {user}, got {res['Location']}"
        print(f"PASS: {user} login redirected to {res['Location']}")

    print("\n--- TEST 3: ACCESS CONTROL & AUTHORIZATION ---")
    # Student attempting to access Private Employee dashboard
    c.login(username='test_student', password='password123')
    res = c.get('/private-employee/dashboard/', follow=False)
    assert res.status_code == 302, f"Expected 302 redirect for student accessing private employee dashboard, got {res.status_code}"
    assert res['Location'] == '/student/dashboard/', f"Expected redirect back to /student/dashboard/, got {res['Location']}"
    print(f"PASS: test_student blocked from /private-employee/dashboard/ -> redirected to {res['Location']}")

    # Private Employee attempting to access Student dashboard
    c.login(username='test_priv_emp', password='password123')
    res = c.get('/student/dashboard/', follow=False)
    assert res.status_code == 302, f"Expected 302 redirect for private employee accessing student dashboard, got {res.status_code}"
    assert res['Location'] == '/private-employee/dashboard/', f"Expected redirect back to /private-employee/dashboard/, got {res['Location']}"
    print(f"PASS: test_priv_emp blocked from /student/dashboard/ -> redirected to {res['Location']}")

    # Job seeker attempting to access Government employee dashboard
    c.login(username='test_job_seeker', password='password123')
    res = c.get('/government-employee/dashboard/', follow=False)
    assert res.status_code == 302
    assert res['Location'] == '/job-seeker/dashboard/'
    print(f"PASS: test_job_seeker blocked from /government-employee/dashboard/ -> redirected to {res['Location']}")

    # Admin accessing all dashboards
    c.login(username='admin', password='admin123')
    for target in [
        '/dashboard/',
        '/student/dashboard/',
        '/working-professional/dashboard/',
        '/government-employee/dashboard/',
        '/private-employee/dashboard/',
        '/business/dashboard/',
        '/job-seeker/dashboard/',
        '/other/dashboard/'
    ]:
        res = c.get(target)
        assert res.status_code == 200, f"Admin expected 200 on {target}, got {res.status_code}"
        print(f"PASS: admin successfully accessed {target} (HTTP 200)")

    print("\n--- TEST 4: CONTENT, DYNAMIC OCCUPATION & SECTION VERIFICATIONS ---")
    # 1. Student dashboard
    c.login(username='test_student', password='password123')
    res = c.get('/student/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'Student ID' in html
    assert 'Attendance' in html
    assert 'Occupation:' in html
    assert 'STUDENT' in html
    assert 'My Complaints & Requests' in html
    assert 'My Visitors & Guests' in html
    print("PASS: Student dashboard content & dynamic occupation verified.")

    # 2. Working Professional dashboard
    c.login(username='test_working_prof', password='password123')
    res = c.get('/working-professional/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'WORKING PROFESSIONAL' in html
    assert 'Occupation:' in html
    assert 'Employee ID' in html
    assert 'Company' in html
    assert 'Maintenance & Service Tickets' in html
    assert 'Guest & Visitor Logs' in html
    print("PASS: Working Professional dashboard content verified.")

    # 3. Government Employee dashboard
    c.login(username='test_gov_emp', password='password123')
    res = c.get('/government-employee/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'GOVERNMENT EMPLOYEE' in html
    assert 'Occupation:' in html
    assert 'Department' in html
    assert 'Government Office' in html
    assert 'Maintenance & Service Tickets' in html
    assert 'Official & Personal Visitors' in html
    print("PASS: Government Employee dashboard content verified.")

    # 4. Private Employee dashboard
    c.login(username='test_priv_emp', password='password123')
    res = c.get('/private-employee/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'PRIVATE EMPLOYEE' in html
    assert 'Occupation:' in html
    assert 'Employee ID' in html
    assert 'Company' in html
    assert 'Workplace Resident Maintenance' in html
    assert 'Guest & Visitor Entry Logs' in html
    print("PASS: Private Employee dashboard content verified.")

    # 5. Business dashboard
    c.login(username='test_business', password='password123')
    res = c.get('/business/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'BUSINESS / SELF EMPLOYED' in html
    assert 'Occupation:' in html
    assert 'Business Profile' in html
    assert 'Enterprise' in html
    assert 'Service & Facility Requests' in html
    assert 'Business Associates & Guests' in html
    print("PASS: Business dashboard content verified.")

    # 6. Job Seeker dashboard
    c.login(username='test_job_seeker', password='password123')
    res = c.get('/job-seeker/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'JOB SEEKER' in html
    assert 'Occupation:' in html
    assert 'Job & Training Updates' in html
    assert 'Qualification' in html
    assert 'Hostel Facility Complaints' in html
    assert 'Visitors & Guest Passes' in html
    print("PASS: Job Seeker dashboard content verified.")

    # 7. Other dashboard
    c.login(username='test_other', password='password123')
    res = c.get('/other/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'OTHER' in html
    assert 'Occupation:' in html
    assert 'My Complaints & Requests' in html
    assert 'My Visitors & Guests' in html
    print("PASS: Other dashboard content verified.")

    # 8. Master Admin Dashboard
    c.login(username='admin', password='admin123')
    res = c.get('/dashboard/')
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert 'Enterprise Control Center' in html or 'Enterprise Administration' in html
    assert 'Resident Occupation Distribution' in html
    assert 'Students' in html
    assert 'Working Professionals' in html
    assert 'Government Employees' in html
    assert 'Private Employees' in html
    assert 'Business / Self Employed' in html
    assert 'Job Seekers' in html
    assert 'Leave Requests' in html
    assert 'Notices' in html
    print("PASS: Master Admin dashboard content verified.")

    print("\n--- TEST 5: LOGOUT VERIFICATION ---")
    logout_res = c.get('/accounts/logout/', follow=False)
    assert logout_res.status_code == 302, f"Expected 302 redirect on logout, got {logout_res.status_code}"
    print(f"PASS: Logout redirected successfully to {logout_res['Location']}")

    print("\n=======================================================")
    print("ALL AUTOMATED TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")
    print("=======================================================")

if __name__ == '__main__':
    setup_users()
    run_tests()
