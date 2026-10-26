from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .forms import (
    LoginForm,
    UserProfileForm,
    UserCreateForm,
    StudentSignupForm,
)

from .models import User
from students.models import Student


# ============================================================
# LOGIN
# ============================================================

def login_view(request):
    from dashboard.security import get_dashboard_url_for_user

    # Already logged-in users
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_for_user(request.user))

    if request.method == 'POST':

        form = LoginForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                f"Welcome back, "
                f"{user.get_full_name() or user.username}!"
            )

            next_url = request.GET.get('next')

            if next_url:
                return redirect(next_url)

            return redirect(get_dashboard_url_for_user(user))

    else:

        form = LoginForm()

    return render(
        request,
        'accounts/login.html',
        {
            'form': form
        }
    )


# ============================================================
# STUDENT SIGNUP
# ============================================================

def signup_view(request):

    # Already logged-in users don't need signup
    if request.user.is_authenticated:
        from dashboard.security import get_dashboard_url_for_user
        return redirect(get_dashboard_url_for_user(request.user))

    if request.method == 'POST':

        form = StudentSignupForm(
            request.POST
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    # ========================================
                    # OCCUPATION
                    # ========================================

                    occupation = form.cleaned_data[
                        'occupation'
                    ]

                    # If user selected Other,
                    # save the entered occupation instead
                    if occupation == 'Other':
                        occupation = form.cleaned_data.get(
                            'other_occupation',
                            ''
                        ).strip() or 'Other'

                    # ========================================
                    # CREATE USER
                    # ========================================

                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password1'],
                        first_name=form.cleaned_data['first_name'],
                        last_name='',
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'],
                        role=User.ROLE_STUDENT,
                        occupation=occupation,
                    )

                    # ========================================
                    # CREATE STUDENT PROFILE
                    # ========================================

                    Student.objects.create(
                        user=user,
                        student_id=form.cleaned_data['student_id'],
                        first_name=form.cleaned_data['first_name'],
                        last_name='',
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'],
                        occupation=occupation,
                        company_name=form.cleaned_data.get('company_name', '').strip(),
                        designation=form.cleaned_data.get('designation', '').strip(),
                        work_location=form.cleaned_data.get('work_location', '').strip(),
                        work_shift=form.cleaned_data.get('work_shift', '').strip(),
                        department=form.cleaned_data.get('department', '').strip(),
                        government_office=form.cleaned_data.get('government_office', '').strip(),
                        office_location=form.cleaned_data.get('office_location', '').strip(),
                        business_name=form.cleaned_data.get('business_name', '').strip(),
                        business_type=form.cleaned_data.get('business_type', '').strip(),
                        business_location=form.cleaned_data.get('business_location', '').strip(),
                        qualification=form.cleaned_data.get('qualification', '').strip(),
                        skills=form.cleaned_data.get('skills', '').strip(),
                        experience=form.cleaned_data.get('experience', '').strip(),
                        preferred_job=form.cleaned_data.get('preferred_job', '').strip(),
                        preferred_location=form.cleaned_data.get('preferred_location', '').strip(),
                        course='',
                        year=1,
                        status=Student.STATUS_ACTIVE,
                    )

                # ============================================
                # SUCCESS
                # ============================================

                messages.success(
                    request,
                    "Account created successfully. "
                    "You can now sign in."
                )

                return redirect(
                    'accounts:login'
                )

            except Exception as e:

                # Don't expose database/system errors
                messages.error(
                    request,
                    "Unable to create your account. "
                    "Please try again."
                )

    else:

        form = StudentSignupForm()

    return render(
        request,
        'accounts/signup.html',
        {
            'form': form
        }
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    messages.info(
        request,
        "You have been logged out successfully."
    )

    return redirect(
        'accounts:login'
    )


# ============================================================
# PROFILE
# ============================================================

@login_required
def profile_view(request):
    profile = getattr(request.user, 'student_profile', None)
    allocation = profile.get_current_allocation() if profile else None

    if request.method == 'POST':
        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            if profile:
                profile.first_name = request.user.first_name
                profile.email = request.user.email
                profile.phone = request.user.phone
                profile.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect(
                'accounts:profile'
            )

    else:
        form = UserProfileForm(
            instance=request.user
        )

    return render(
        request,
        'accounts/profile.html',
        {
            'form': form,
            'profile': profile,
            'allocation': allocation,
        }
    )


# ============================================================
# USER LIST
# ============================================================

@login_required
def user_list_view(request):

    """
    Admin-only:
    Display all registered users.
    """

    # ----------------------------------------
    # ADMIN CHECK
    # ----------------------------------------

    if not request.user.is_admin:

        messages.error(
            request,
            "Access denied."
        )

        return redirect(
            'dashboard:index'
        )

    # ----------------------------------------
    # GET USERS
    # ----------------------------------------

    users = User.objects.all().order_by(
        '-date_joined'
    )

    return render(
        request,
        'accounts/user_list.html',
        {
            'users': users
        }
    )


# ============================================================
# CREATE USER
# ============================================================

@login_required
def user_create_view(request):

    """
    Admin-only:
    Create a new user from admin panel.
    """

    # ----------------------------------------
    # ADMIN CHECK
    # ----------------------------------------

    if not request.user.is_admin:

        messages.error(
            request,
            "Access denied."
        )

        return redirect(
            'dashboard:index'
        )

    # ----------------------------------------
    # POST
    # ----------------------------------------

    if request.method == 'POST':

        form = UserCreateForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "User created successfully."
            )

            return redirect(
                'accounts:user_list'
            )

    # ----------------------------------------
    # GET
    # ----------------------------------------

    else:

        form = UserCreateForm()

    return render(
        request,
        'accounts/user_form.html',
        {
            'form': form,
            'title': 'Create User'
        }
    )