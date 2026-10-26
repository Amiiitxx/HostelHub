from django import forms
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'email', 'phone',
            'gender', 'date_of_birth', 'course', 'year', 'address', 'city', 'state',
            'guardian_name', 'guardian_phone', 'guardian_relation',
            'photo', 'id_document', 'status',
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. STU2024001'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 99999 99999'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'course': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech Computer Science'}),
            'year': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Guardian's full name"}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Guardian's phone"}),
            'guardian_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Father, Mother'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'id_document': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
