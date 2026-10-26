from django.db import models
from django.utils import timezone
from students.models import Student


class Visitor(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('inside', 'Currently Inside'),
        ('completed', 'Completed'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='visitors'
    )

    visitor_name = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=20
    )

    relation = models.CharField(
        max_length=50,
        blank=True
    )

    purpose = models.CharField(
        max_length=200,
        blank=True
    )

    visit_date = models.DateField(
        null=True,
        blank=True
    )

    expected_arrival = models.TimeField(
        null=True,
        blank=True
    )

    expected_departure = models.TimeField(
        null=True,
        blank=True
    )

    check_in = models.DateTimeField(
        null=True,
        blank=True
    )

    check_out = models.DateTimeField(
        null=True,
        blank=True
    )

    id_proof = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    registered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_visitors'
    )

    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_visitors'
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    rejected_reason = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['check_in']),
            models.Index(fields=['student']),
            models.Index(fields=['status']),
            models.Index(fields=['visit_date']),
        ]

    def __str__(self):
        return f"{self.visitor_name} → {self.student.full_name}"

    @property
    def name(self):
        return self.visitor_name

    @property
    def is_inside(self):
        return (
            self.status == 'inside'
            and self.check_in is not None
            and self.check_out is None
        )

    @property
    def duration(self):

        if self.check_in and self.check_out:

            delta = self.check_out - self.check_in

            hours = int(
                delta.total_seconds() // 3600
            )

            mins = int(
                (delta.total_seconds() % 3600) // 60
            )

            return f"{hours}h {mins}m"

        if self.is_inside:

            delta = timezone.now() - self.check_in

            hours = int(
                delta.total_seconds() // 3600
            )

            mins = int(
                (delta.total_seconds() % 3600) // 60
            )

            return f"{hours}h {mins}m"

        return "-"

    def do_checkout(self):

        self.check_out = timezone.now()
        self.status = 'completed'

        self.save(
            update_fields=[
                'check_out',
                'status'
            ]
        )