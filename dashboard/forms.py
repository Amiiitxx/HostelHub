from django import forms
from django.utils import timezone
from accounts.models import User, WardenProfile
from hostel.models import Building
from .models import Notice
from attendance.models import LeaveRequest


class WardenCreateForm(forms.Form):
    first_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username (for login)'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    employee_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID (e.g. WRD-101)'})
    )
    assigned_hostel = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        required=False,
        empty_label="Select Assigned Hostel / Building",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assigned_block = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Block / Wing (e.g. Block A, East Wing)'})
    )
    joining_date = forms.DateField(
        initial=timezone.now,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary Password'})
    )
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_employee_id(self):
        emp_id = self.cleaned_data.get('employee_id')
        if WardenProfile.objects.filter(employee_id__iexact=emp_id).exists():
            raise forms.ValidationError("This Employee ID is already in use.")
        return emp_id


class WardenEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = WardenProfile
        fields = [
            'employee_id',
            'phone',
            'assigned_hostel',
            'assigned_block',
            'status',
            'joining_date',
            'profile_photo',
            'notes',
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_hostel': forms.Select(attrs={'class': 'form-select'}),
            'assigned_block': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = [
            'title',
            'category',
            'target_scope',
            'target_hostel',
            'target_occupation',
            'content',
            'is_published',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notice Title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'target_scope': forms.Select(attrs={'class': 'form-select', 'id': 'id_target_scope'}),
            'target_hostel': forms.Select(attrs={'class': 'form-select'}),
            'target_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Student, Working Professional'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Notice Announcement Content...'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
