from django.db import models
from django.conf import settings


class Student(models.Model):

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_GRADUATED = 'graduated'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_GRADUATED, 'Graduated'),
    ]

    YEAR_CHOICES = [
        (i, f'Year {i}')
        for i in range(1, 7)
    ]

    # ============================================================
    # USER
    # ============================================================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True,
    )

    # ============================================================
    # BASIC DETAILS
    # ============================================================

    student_id = models.CharField(
        max_length=30,
        unique=True
    )

    first_name = models.CharField(
        max_length=80
    )

    last_name = models.CharField(
        max_length=80
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=20
    )

    occupation = models.CharField(
        max_length=100,
        blank=True
    )

    # ============================================================
    # PROFESSIONAL & OCCUPATION DETAILS
    # ============================================================

    company_name = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    work_location = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    work_shift = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    # Government Employee Specific Details
    department = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    government_office = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    office_location = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    # Business / Self Employed Specific Details
    business_name = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    business_type = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    business_location = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    # Job Seeker Specific Details
    qualification = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    skills = models.CharField(
        max_length=250,
        blank=True,
        default=''
    )

    experience = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    preferred_job = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    preferred_location = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    # ============================================================
    # ACADEMIC DETAILS
    # ============================================================

    course = models.CharField(
        max_length=100
    )

    year = models.IntegerField(
        choices=YEAR_CHOICES,
        default=1
    )

    # ============================================================
    # PERSONAL DETAILS
    # ============================================================

    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        default='male'
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=80,
        blank=True
    )

    state = models.CharField(
        max_length=80,
        blank=True
    )

    # ============================================================
    # GUARDIAN
    # ============================================================

    guardian_name = models.CharField(
        max_length=100,
        blank=True
    )

    guardian_phone = models.CharField(
        max_length=20,
        blank=True
    )

    guardian_relation = models.CharField(
        max_length=50,
        blank=True
    )

    # ============================================================
    # DOCUMENTS
    # ============================================================

    photo = models.ImageField(
        upload_to='students/photos/',
        blank=True,
        null=True
    )

    id_document = models.FileField(
        upload_to='students/documents/',
        blank=True,
        null=True
    )

    # ============================================================
    # STATUS
    # ============================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )

    admission_date = models.DateField(
        auto_now_add=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ============================================================
    # META
    # ============================================================

    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(
                fields=['student_id']
            ),
            models.Index(
                fields=['status']
            ),
            models.Index(
                fields=['course']
            ),
            models.Index(
                fields=['occupation']
            ),
        ]

    # ============================================================
    # STRING REPRESENTATION
    # ============================================================

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

    # ============================================================
    # FULL NAME & IDENTIFIERS
    # ============================================================

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        if name:
            return name
        if self.user and (self.user.get_full_name() or self.user.username):
            return self.user.get_full_name() or self.user.username
        return "Resident"

    @property
    def employee_id(self):
        return self.student_id

    # ============================================================
    # INITIALS
    # ============================================================

    @property
    def initials(self):
        return (
            f"{self.first_name[:1]}"
            f"{self.last_name[:1]}"
        ).upper()

    # ============================================================
    # CURRENT ROOM ALLOCATION
    # ============================================================

    def get_current_allocation(self):
        return self.allocations.filter(
            status='active'
        ).first()

    # ============================================================
    # PENDING FEES
    # ============================================================

    def get_pending_fees_total(self):
        from fees.models import Fee

        return Fee.objects.filter(
            student=self,
            status__in=['pending', 'overdue']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    # ============================================================
    # ATTENDANCE PERCENTAGE
    # ============================================================

    def get_attendance_percentage(self):

        from attendance.models import Attendance

        total = Attendance.objects.filter(
            student=self
        ).count()

        if total == 0:
            return 0

        present = Attendance.objects.filter(
            student=self,
            status='present'
        ).count()

        return round(
            (present / total) * 100,
            1
        )