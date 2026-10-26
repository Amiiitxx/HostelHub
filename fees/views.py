from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Fee, Payment
from students.models import Student


def staff_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if not request.user.can_manage_hostel:
            messages.error(request, "Access denied.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def fee_list(request):
    qs = Fee.objects.select_related('student')
    if request.user.is_student_role:
        try:
            qs = qs.filter(student=request.user.student_profile)
        except Exception:
            qs = Fee.objects.none()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) | Q(student__student_id__icontains=q))

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    fee_type = request.GET.get('fee_type', '')
    if fee_type:
        qs = qs.filter(fee_type=fee_type)

    # Summary stats
    totals = qs.aggregate(
        total=Sum('amount'),
        paid=Sum('amount', filter=Q(status='paid')),
        pending=Sum('amount', filter=Q(status='pending')),
        overdue=Sum('amount', filter=Q(status='overdue')),
    )

    paginator = Paginator(qs.order_by('-created_at'), 20)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'fees/list.html', {
        'fees': page,
        'q': q,
        'status_filter': status,
        'fee_type_filter': fee_type,
        'totals': totals,
        'fee_types': Fee.FEE_TYPES,
        'total_count': qs.count(),
    })


@login_required
def fee_detail(request, pk):
    fee = get_object_or_404(Fee.objects.select_related('student'), pk=pk)
    if request.user.is_student_role:
        try:
            if request.user.student_profile != fee.student:
                messages.error(request, "Access denied.")
                return redirect('dashboard:index')
        except Exception:
            return redirect('dashboard:index')
    payments = fee.payments.all().order_by('-paid_at')
    return render(request, 'fees/detail.html', {'fee': fee, 'payments': payments})


@staff_required
def fee_create(request):
    students = Student.objects.filter(status='active').order_by('first_name')
    preselect = request.GET.get('student')
    if request.method == 'POST':
        student_id = request.POST.get('student')
        fee_type = request.POST.get('fee_type')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        description = request.POST.get('description', '')
        try:
            fee = Fee.objects.create(
                student_id=student_id,
                fee_type=fee_type,
                amount=amount,
                due_date=due_date,
                description=description,
                created_by=request.user,
            )
            fee.update_status()
            messages.success(request, f"Fee of ₹{amount} created for {fee.student.full_name}.")
            return redirect('fees:detail', pk=fee.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'fees/form.html', {
        'students': students,
        'fee_types': Fee.FEE_TYPES,
        'preselect': preselect,
        'today': timezone.now().date(),
    })


@staff_required
def payment_create(request, fee_pk):
    fee = get_object_or_404(Fee, pk=fee_pk)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('payment_method')
        ref = request.POST.get('transaction_reference', '')
        notes = request.POST.get('notes', '')
        try:
            payment = Payment.objects.create(
                fee=fee,
                amount=amount,
                payment_method=method,
                transaction_reference=ref,
                notes=notes,
                recorded_by=request.user,
            )
            messages.success(request, f"Payment of ₹{amount} recorded. Receipt: {payment.receipt_number}")
            return redirect('fees:receipt', pk=payment.pk)
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'fees/payment_form.html', {
        'fee': fee,
        'payment_methods': Payment.PAYMENT_METHODS,
        'balance': fee.balance,
    })


@login_required
def receipt_view(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('fee__student'), pk=pk)
    return render(request, 'fees/receipt.html', {'payment': payment})


@staff_required
def fee_delete(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    if request.method == 'POST':
        student = fee.student.full_name
        fee.delete()
        messages.success(request, f"Fee deleted for {student}.")
        return redirect('fees:list')
    return redirect('fees:list')
