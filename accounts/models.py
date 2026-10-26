from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    # Roles
    ROLE_ADMIN = 'admin'
    ROLE_WARDEN = 'warden'
    ROLE_STUDENT = 'student'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_WARDEN, 'Warden'),
        (ROLE_STUDENT, 'Student'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT
    )

    # Occupation
    OCCUPATION_STUDENT = 'Student'
    OCCUPATION_WORKING_PROFESSIONAL = 'Working Professional'
    OCCUPATION_GOVERNMENT_EMPLOYEE = 'Government Employee'
    OCCUPATION_PRIVATE_EMPLOYEE = 'Private Employee'
    OCCUPATION_BUSINESS = 'Business / Self Employed'
    OCCUPATION_JOB_SEEKER = 'Job Seeker'
    OCCUPATION_OTHER = 'Other'

    OCCUPATION_CHOICES = [
        (OCCUPATION_STUDENT, 'Student'),
        (OCCUPATION_WORKING_PROFESSIONAL, 'Working Professional'),
        (OCCUPATION_GOVERNMENT_EMPLOYEE, 'Government Employee'),
        (OCCUPATION_PRIVATE_EMPLOYEE, 'Private Employee'),
        (OCCUPATION_BUSINESS, 'Business / Self Employed'),
        (OCCUPATION_JOB_SEEKER, 'Job Seeker'),
        (OCCUPATION_OTHER, 'Other'),
    ]

    occupation = models.CharField(
        max_length=60,
        choices=OCCUPATION_CHOICES,
        default=OCCUPATION_STUDENT
    )

    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != self.ROLE_ADMIN:
            self.role = self.ROLE_ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_warden(self):
        return self.role == self.ROLE_WARDEN

    @property
    def is_student_role(self):
        return self.role == self.ROLE_STUDENT and not self.is_superuser

    @property
    def can_manage_hostel(self):
        """Admin and Warden can manage hostel operations."""
        return self.role in [self.ROLE_ADMIN, self.ROLE_WARDEN] or self.is_superuser or self.is_staff

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def is_warden_profile(self):
        return hasattr(self, 'warden_profile')


class WardenProfile(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='warden_profile'
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True
    )
    assigned_hostel = models.ForeignKey(
        'hostel.Building',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wardens'
    )
    assigned_block = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    joining_date = models.DateField(
        null=True,
        blank=True
    )
    profile_photo = models.ImageField(
        upload_to='wardens/',
        blank=True,
        null=True
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Warden Profile'
        verbose_name_plural = 'Warden Profiles'
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        hostel_str = f" ({self.assigned_hostel.name})" if self.assigned_hostel else " (Unassigned)"
        return f"{self.user.get_full_name() or self.user.username} - {self.employee_id}{hostel_str}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE and self.user.is_active