from django.db import models
from django.utils import timezone


class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('General', 'General Notice'),
        ('Facility', 'Facility & Maintenance'),
        ('Dining', 'Dining & Mess'),
        ('Security', 'Security & Rules'),
        ('Urgent', 'Urgent Announcement'),
    ]

    SCOPE_CHOICES = [
        ('all', 'All Residents'),
        ('hostel', 'Specific Hostel'),
        ('occupation', 'Specific Occupation'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General')
    target_scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='all')
    target_hostel = models.ForeignKey(
        'hostel.Building',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notices'
    )
    target_occupation = models.CharField(max_length=60, blank=True, default='')
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.title}"
