"""
JAK Data Analytics
Authentication Package

Handles:
- User Login
- User Registration
- Password Recovery
- User Logout
"""

from .login import render_login_page
from .register import render_registration_page
from .forgot_password import render_forgot_password_page
from .logout import render_logout_page, logout_user


__all__ = [
    "render_login_page",
    "render_registration_page",
    "render_forgot_password_page",
    "render_logout_page",
    "logout_user",
]