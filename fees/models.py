from django.db import models
from django.utils import timezone
from students.models import Student


class Fee(models.Model):
    TYPE_HOSTEL = 'hostel'
    TYPE_MESS = 'mess'
    TYPE_LAUNDRY = 'laundry'
    TYPE_ELECTRICITY = 'electricity'
    TYPE_MAINTENANCE = 'maintenance'
    TYPE_FINE = 'fine'
    TYPE_OTHER = 'other'

    FEE_TYPES = [
        (TYPE_HOSTEL, 'Hostel Fee'),
        (TYPE_MESS, 'Mess Fee'),
        (TYPE_LAUNDRY, 'Laundry Fee'),
        (TYPE_ELECTRICITY, 'Electricity Fee'),
        (TYPE_MAINTENANCE, 'Maintenance Fee'),
        (TYPE_FINE, 'Fine'),
        (TYPE_OTHER, 'Other'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_PARTIAL = 'partial'

    FEE_STATUSES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_PARTIAL, 'Partial'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default=TYPE_HOSTEL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    description = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=FEE_STATUSES, default=STATUS_PENDING)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.get_fee_type_display()} — ₹{self.amount}"

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance(self):
        return self.amount - self.total_paid

    def update_status(self):
        paid = self.total_paid
        if paid >= self.amount:
            self.status = self.STATUS_PAID
        elif paid > 0:
            self.status = self.STATUS_PARTIAL
        elif self.due_date < timezone.now().date():
            self.status = self.STATUS_OVERDUE
        else:
            self.status = self.STATUS_PENDING
        self.save(update_fields=['status'])


class Payment(models.Model):
    METHOD_CASH = 'cash'
    METHOD_BANK = 'bank_transfer'
    METHOD_UPI = 'upi'
    METHOD_CHEQUE = 'cheque'
    METHOD_OTHER = 'other'

    PAYMENT_METHODS = [
        (METHOD_CASH, 'Cash'),
        (METHOD_BANK, 'Bank Transfer'),
        (METHOD_UPI, 'UPI'),
        (METHOD_CHEQUE, 'Cheque'),
        (METHOD_OTHER, 'Other'),
    ]

    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default=METHOD_CASH)
    transaction_reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    receipt_number = models.CharField(max_length=30, unique=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"Payment ₹{self.amount} for {self.fee}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import random, string
            self.receipt_number = 'RCP' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)
        self.fee.update_status()
