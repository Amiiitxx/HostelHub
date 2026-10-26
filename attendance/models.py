from django.db import models
from students.models import Student


class Attendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LEAVE = 'leave'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LEAVE, 'On Leave'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    marked_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student__first_name']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['student', 'date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.date} — {self.get_status_display()}"


class LeaveRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    LEAVE_TYPES = [
        ('Home Visit', 'Home Visit / Weekend'),
        ('Medical', 'Medical Leave'),
        ('Academic', 'Academic / Seminar'),
        ('Work Outstation', 'Work Outstation / Shift'),
        ('Emergency', 'Family Emergency'),
        ('Other', 'Other Leave'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.CharField(
        max_length=50,
        choices=LEAVE_TYPES,
        default='Home Visit'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    action_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actioned_leaves'
    )
    action_remarks = models.TextField(
        blank=True,
        default=''
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.leave_type} ({self.get_status_display()})"

    @property
    def total_days(self):
        delta = self.end_date - self.start_date
        return max(1, delta.days + 1)
