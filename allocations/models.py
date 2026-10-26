from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from students.models import Student
from hostel.models import Bed


class Allocation(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_VACATED = 'vacated'
    STATUS_TRANSFERRED = 'transferred'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_VACATED, 'Vacated'),
        (STATUS_TRANSFERRED, 'Transferred'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='allocations')
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='allocations')
    allocated_date = models.DateField(default=timezone.now)
    vacated_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    notes = models.TextField(blank=True)
    allocated_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='allocated_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['bed', 'status']),
        ]

    def __str__(self):
        return f"{self.student.full_name} → {self.bed.full_name}"

    def clean(self):
        if self.status == self.STATUS_ACTIVE:
            # Rule 1: Bed cannot have multiple active allocations
            qs = Allocation.objects.filter(bed=self.bed, status=self.STATUS_ACTIVE)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("This bed is already allocated to another student.")

            # Rule 2: Student cannot have multiple active allocations
            qs2 = Allocation.objects.filter(student=self.student, status=self.STATUS_ACTIVE)
            if self.pk:
                qs2 = qs2.exclude(pk=self.pk)
            if qs2.exists():
                raise ValidationError("This student already has an active allocation.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Sync bed status
        if self.status == self.STATUS_ACTIVE:
            self.bed.status = 'occupied'
        else:
            # Check if any other active allocation for this bed
            if not Allocation.objects.filter(bed=self.bed, status=self.STATUS_ACTIVE).exclude(pk=self.pk).exists():
                self.bed.status = 'available'
        self.bed.save(update_fields=['status'])

    def vacate(self, user=None):
        """Vacate this allocation and free the bed."""
        self.status = self.STATUS_VACATED
        self.vacated_date = timezone.now().date()
        self.save()

    @property
    def duration_days(self):
        end = self.vacated_date or timezone.now().date()
        return (end - self.allocated_date).days
