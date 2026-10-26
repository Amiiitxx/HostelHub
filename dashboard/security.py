from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

OCCUPATION_URL_MAP = {
    'student': '/student/dashboard/',
    'working_professional': '/working-professional/dashboard/',
    'government_employee': '/government-employee/dashboard/',
    'private_employee': '/private-employee/dashboard/',
    'business': '/business/dashboard/',
    'job_seeker': '/job-seeker/dashboard/',
    'other': '/other/dashboard/',
}


def normalize_occupation(occ):
    """
    Normalizes any occupation string or choice to a canonical key.
    """
    if not occ:
        return 'other'
    occ_str = str(occ).strip().lower().replace('-', '_').replace(' ', '_').replace('/', '_')
    if 'student' in occ_str:
        return 'student'
    if 'working_prof' in occ_str or 'working_professional' in occ_str:
        return 'working_professional'
    if 'gov' in occ_str:
        return 'government_employee'
    if 'priv' in occ_str:
        return 'private_employee'
    if 'busin' in occ_str or 'self' in occ_str:
        return 'business'
    if 'job' in occ_str or 'seeker' in occ_str:
        return 'job_seeker'
    return 'other'


def get_user_occupation(user):
    """
    Get the canonical occupation for a user, prioritizing student_profile then user.occupation.
    """
    if not user or not user.is_authenticated:
        return 'other'
    sp = getattr(user, 'student_profile', None)
    if sp and sp.occupation:
        return sp.occupation
    if hasattr(user, 'occupation') and user.occupation:
        return user.occupation
    return 'other'


def get_dashboard_url_for_user(user):
    """
    Returns the appropriate dashboard URL for the user.
    Admin / Superuser -> /dashboard/
    Warden -> /warden/dashboard/
    Occupation users -> /<occupation-slug>/dashboard/
    """
    if (
        getattr(user, 'is_admin', False)
        or getattr(user, 'is_superuser', False)
        or (getattr(user, 'role', '') == 'admin')
    ):
        return '/dashboard/'

    if getattr(user, 'is_warden', False) or (getattr(user, 'role', '') == 'warden'):
        return '/warden/dashboard/'

    occ = get_user_occupation(user)
    norm = normalize_occupation(occ)
    return OCCUPATION_URL_MAP.get(norm, '/other/dashboard/')


def admin_required(view_func):
    """
    Decorator for strictly Admin-only routes.
    Residents and Wardens are strictly blocked from accessing these routes.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        is_adm = (
            getattr(request.user, 'is_admin', False)
            or getattr(request.user, 'is_superuser', False)
            or (getattr(request.user, 'role', '') == 'admin')
        )

        if not is_adm:
            messages.error(
                request,
                "Access restricted: Master Admin authorization required."
            )
            return redirect(get_dashboard_url_for_user(request.user))

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def warden_required(view_func):
    """
    Decorator for Warden routes.
    Admins are also permitted, but Residents are strictly blocked.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        can_access = (
            getattr(request.user, 'is_warden', False)
            or getattr(request.user, 'is_admin', False)
            or getattr(request.user, 'is_superuser', False)
            or getattr(request.user, 'role', '') in ['warden', 'admin']
        )

        if not can_access:
            messages.error(
                request,
                "Access restricted: Warden authorization required."
            )
            return redirect(get_dashboard_url_for_user(request.user))

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def occupation_required(allowed_occupation_key):
    """
    Decorator for occupation-specific dashboards.
    - If user is not authenticated -> redirect to login.
    - If user is admin or warden -> allow access.
    - If user's occupation matches allowed_occupation_key -> allow access.
    - If user's occupation does NOT match -> redirect to their own dashboard with warning.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            # Admin, warden, and superuser can view any dashboard
            if (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'is_warden', False)
                or getattr(request.user, 'is_superuser', False)
                or (getattr(request.user, 'role', '') in ['admin', 'warden'])
            ):
                return view_func(request, *args, **kwargs)

            user_occ = get_user_occupation(request.user)
            user_norm = normalize_occupation(user_occ)
            target_norm = normalize_occupation(allowed_occupation_key)

            if user_norm != target_norm:
                messages.warning(
                    request,
                    f"Access denied to {allowed_occupation_key.replace('_', ' ').title()} Dashboard. Redirected to your dashboard."
                )
                return redirect(get_dashboard_url_for_user(request.user))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
