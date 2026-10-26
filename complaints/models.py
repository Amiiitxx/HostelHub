from django.db import models
from django.utils import timezone
from students.models import Student


class Complaint(models.Model):
    CAT_MAINTENANCE = 'maintenance'
    CAT_ELECTRICAL = 'electrical'
    CAT_PLUMBING = 'plumbing'
    CAT_CLEANING = 'cleaning'
    CAT_FOOD = 'food'
    CAT_SECURITY = 'security'
    CAT_OTHER = 'other'

    CATEGORIES = [
        (CAT_MAINTENANCE, 'Maintenance'),
        (CAT_ELECTRICAL, 'Electrical'),
        (CAT_PLUMBING, 'Plumbing'),
        (CAT_CLEANING, 'Cleaning'),
        (CAT_FOOD, 'Food'),
        (CAT_SECURITY, 'Security'),
        (CAT_OTHER, 'Other'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CRITICAL = 'critical'

    PRIORITIES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'

    STATUSES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='complaints')
    category = models.CharField(max_length=20, choices=CATEGORIES, default=CAT_OTHER)
    priority = models.CharField(max_length=20, choices=PRIORITIES, default=PRIORITY_MEDIUM)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_complaints'
    )
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['student']),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} — {self.student.full_name}"

    def resolve(self):
        self.status = self.STATUS_RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=['status', 'resolved_at'])

    @property
    def resolution_time_hours(self):
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return round(delta.total_seconds() / 3600, 1)
        return None


class ComplaintUpdate(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=Complaint.STATUSES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Update on {self.complaint.title} at {self.created_at}"
