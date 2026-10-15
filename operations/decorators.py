"""
Role-based access control decorators for QualiTrack.
Ensures that only users with the required role can access specific views.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """
    Decorator for views that checks if the logged-in user has one of the allowed roles.
    allowed_roles: string (e.g. 'ADMIN') or list of strings (e.g. ['SUPERVISOR', 'ADMIN'])
    
    If the user is not authenticated -> redirects to login page.
    If the user has the wrong role -> blocks access, displays clear error,
    and redirects them safely to their own assigned dashboard.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Require authentication
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('login')

            # 2. Determine user's active role
            profile = getattr(request.user, 'profile', None)
            user_role = profile.role if profile else ('ADMIN' if request.user.is_superuser else None)

            # 3. Superusers have admin privileges
            if request.user.is_superuser and 'ADMIN' in allowed_roles:
                return view_func(request, *args, **kwargs)

            # 4. Check if user's role is in allowed_roles
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # 5. Access Denied: Show message and redirect to user's proper dashboard
            role_display = dict(profile.ROLE_CHOICES).get(user_role, user_role) if profile else "Unknown"
            messages.error(
                request,
                f"Access Denied: Your assigned role is '{role_display}'. You do not have permission to view that section."
            )

            if user_role == 'INSPECTOR':
                return redirect('inspector_dashboard')
            elif user_role == 'SUPERVISOR':
                return redirect('supervisor_dashboard')
            elif user_role == 'ADMIN' or request.user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('home')

        return _wrapped_view
    return decorator
