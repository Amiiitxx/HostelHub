from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User
from students.models import Student


# ============================================================
# LOGIN FORM
# ============================================================

class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter a name',
                'autofocus': True,
                'autocomplete': 'off',
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Password',
                'autocomplete': 'new-password',
            }
        )
    )


# ============================================================
# USER PROFILE FORM
# ============================================================

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'avatar',
        ]

        widgets = {
            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'avatar': forms.FileInput(
                attrs={
                    'class': 'form-control',
                }
            ),
        }


# ============================================================
# ADMIN USER CREATE FORM
# ============================================================

class UserCreateForm(forms.ModelForm):

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
        ]

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),

            'role': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
        }

    def clean_password2(self):

        p1 = self.cleaned_data.get(
            'password1'
        )

        p2 = self.cleaned_data.get(
            'password2'
        )

        if p1 and p2 and p1 != p2:

            raise forms.ValidationError(
                "Passwords do not match."
            )

        return p2

    def save(self, commit=True):

        user = super().save(
            commit=False
        )

        user.set_password(
            self.cleaned_data['password1']
        )

        if commit:
            user.save()

        return user


# ============================================================
# STUDENT SIGNUP FORM
# ============================================================

class StudentSignupForm(forms.Form):

    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    username = forms.CharField(
        max_length=150,
        label='Username',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username',
            }
        )
    )

    # --------------------------------------------------------
    # FULL NAME
    # --------------------------------------------------------

    first_name = forms.CharField(
        max_length=80,
        label='Full Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Full name',
                'autocomplete': 'name',
            }
        )
    )

    # --------------------------------------------------------
    # STUDENT ID
    # --------------------------------------------------------

    student_id = forms.CharField(
        max_length=30,
        label='Student ID',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Student ID',
            }
        )
    )

    # --------------------------------------------------------
    # PHONE NUMBER
    # --------------------------------------------------------

    phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Phone number',
                'autocomplete': 'tel',
            }
        )
    )

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email address',
                'autocomplete': 'email',
            }
        )
    )

    # --------------------------------------------------------
    # OCCUPATION
    # --------------------------------------------------------

    occupation = forms.ChoiceField(
        label='Occupation',

        choices=[
            ('Student', 'Student'),

            (
                'Working Professional',
                'Working Professional'
            ),

            (
                'Government Employee',
                'Government Employee'
            ),

            (
                'Private Employee',
                'Private Employee'
            ),

            (
                'Business / Self Employed',
                'Business / Self Employed'
            ),

            (
                'Job Seeker',
                'Job Seeker'
            ),

            (
                'Other',
                'Other'
            ),
        ],

        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'id': 'id_occupation',
            }
        )
    )

    # --------------------------------------------------------
    # OTHER OCCUPATION
    # --------------------------------------------------------

    other_occupation = forms.CharField(
        max_length=100,
        required=False,
        label='Specify Occupation',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your occupation',
                'autocomplete': 'organization-title',
                'id': 'id_other_occupation',
            }
        )
    )

    # ========================================================
    # PROFESSIONAL DETAILS
    # ========================================================

    # --------------------------------------------------------
    # COMPANY NAME
    # --------------------------------------------------------

    company_name = forms.CharField(
        max_length=200,
        required=False,
        label='Company Name',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name',
                'id': 'id_company_name',
                'autocomplete': 'organization',
            }
        )
    )

    # --------------------------------------------------------
    # DESIGNATION
    # --------------------------------------------------------

    designation = forms.CharField(
        max_length=150,
        required=False,
        label='Designation',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your designation',
                'id': 'id_designation',
                'autocomplete': 'organization-title',
            }
        )
    )

    # --------------------------------------------------------
    # WORK LOCATION
    # --------------------------------------------------------

    work_location = forms.CharField(
        max_length=200,
        required=False,
        label='Work Location',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter work location',
                'id': 'id_work_location',
            }
        )
    )

    # --------------------------------------------------------
    # WORK SHIFT
    # --------------------------------------------------------

    work_shift = forms.CharField(
        max_length=100,
        required=False,
        label='Work Shift',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Example: 9 AM - 6 PM',
                'id': 'id_work_shift',
            }
        )
    )

    department = forms.CharField(
        max_length=150,
        required=False,
        label='Department',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Revenue, Education, Health',
                'id': 'id_department',
            }
        )
    )

    government_office = forms.CharField(
        max_length=200,
        required=False,
        label='Government Office',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Office / Secretariat Name',
                'id': 'id_government_office',
            }
        )
    )

    office_location = forms.CharField(
        max_length=200,
        required=False,
        label='Office Location',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Office City / Complex',
                'id': 'id_office_location',
            }
        )
    )

    business_name = forms.CharField(
        max_length=200,
        required=False,
        label='Business Name',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enterprise / Trade Name',
                'id': 'id_business_name',
            }
        )
    )

    business_type = forms.CharField(
        max_length=150,
        required=False,
        label='Business Type',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Retail, Tech Services, Trading',
                'id': 'id_business_type',
            }
        )
    )

    business_location = forms.CharField(
        max_length=200,
        required=False,
        label='Business Location',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Business Address / City',
                'id': 'id_business_location',
            }
        )
    )

    qualification = forms.CharField(
        max_length=150,
        required=False,
        label='Qualification',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Highest Degree / Certification',
                'id': 'id_qualification',
            }
        )
    )

    skills = forms.CharField(
        max_length=250,
        required=False,
        label='Skills',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Key Skills & Technologies',
                'id': 'id_skills',
            }
        )
    )

    experience = forms.CharField(
        max_length=100,
        required=False,
        label='Experience',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Fresher, 2 years',
                'id': 'id_experience',
            }
        )
    )

    preferred_job = forms.CharField(
        max_length=150,
        required=False,
        label='Preferred Job',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Target Role / Job Profile',
                'id': 'id_preferred_job',
            }
        )
    )

    preferred_location = forms.CharField(
        max_length=150,
        required=False,
        label='Preferred Location',

        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Preferred Job Location',
                'id': 'id_preferred_location',
            }
        )
    )

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    password1 = forms.CharField(
        label='Password',

        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Create a password',
                'autocomplete': 'new-password',
            }
        )
    )

    # --------------------------------------------------------
    # CONFIRM PASSWORD
    # --------------------------------------------------------

    password2 = forms.CharField(
        label='Confirm Password',

        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Confirm password',
                'autocomplete': 'new-password',
            }
        )
    )

    # ========================================================
    # USERNAME VALIDATION
    # ========================================================

    def clean_username(self):

        username = self.cleaned_data[
            'username'
        ].strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    # ========================================================
    # EMAIL VALIDATION
    # ========================================================

    def clean_email(self):

        email = self.cleaned_data[
            'email'
        ].strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "This email is already registered."
            )

        if Student.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    # ========================================================
    # STUDENT ID VALIDATION
    # ========================================================

    def clean_student_id(self):

        student_id = self.cleaned_data[
            'student_id'
        ].strip()

        if Student.objects.filter(
            student_id__iexact=student_id
        ).exists():

            raise forms.ValidationError(
                "This student ID is already registered."
            )

        return student_id

    # ========================================================
    # PHONE VALIDATION
    # ========================================================

    def clean_phone(self):

        phone = self.cleaned_data[
            'phone'
        ].strip()

        if not phone:

            raise forms.ValidationError(
                "Phone number is required."
            )

        return phone

    # ========================================================
    # FULL NAME VALIDATION
    # ========================================================

    def clean_first_name(self):

        name = self.cleaned_data[
            'first_name'
        ].strip()

        if not name:

            raise forms.ValidationError(
                "Full name is required."
            )

        return name

    # ========================================================
    # OCCUPATION VALIDATION
    # ========================================================

    def clean(self):

        cleaned_data = super().clean()

        occupation = cleaned_data.get(
            'occupation'
        )

        other_occupation = cleaned_data.get(
            'other_occupation'
        )

        # ----------------------------------------------------
        # OTHER OCCUPATION
        # ----------------------------------------------------

        if occupation == 'Other':

            if (
                not other_occupation
                or not other_occupation.strip()
            ):

                self.add_error(
                    'other_occupation',
                    'Please enter your occupation.'
                )

        # ----------------------------------------------------
        # PROFESSIONAL OCCUPATIONS
        # ----------------------------------------------------

        professional_occupations = [
            'Working Professional',
            'Government Employee',
            'Private Employee',
        ]

        if occupation == 'Government Employee':

            if not cleaned_data.get(
                'company_name'
            ):
                cleaned_data['company_name'] = (
                    cleaned_data.get(
                        'government_office'
                    )
                    or cleaned_data.get(
                        'department'
                    )
                    or 'Government Office'
                )

            if not cleaned_data.get(
                'designation'
            ):
                cleaned_data['designation'] = (
                    'Officer'
                )

            if not cleaned_data.get(
                'work_location'
            ):
                cleaned_data['work_location'] = (
                    cleaned_data.get(
                        'office_location'
                    )
                    or 'District Office'
                )

            if not cleaned_data.get(
                'work_shift'
            ):
                cleaned_data['work_shift'] = (
                    '9:30 AM - 5:30 PM'
                )

        if occupation in professional_occupations:

            company_name = cleaned_data.get(
                'company_name'
            )

            designation = cleaned_data.get(
                'designation'
            )

            work_location = cleaned_data.get(
                'work_location'
            )

            work_shift = cleaned_data.get(
                'work_shift'
            )

            if (
                not company_name
                or not company_name.strip()
            ):

                self.add_error(
                    'company_name',
                    'Company name is required.'
                )

            if (
                not designation
                or not designation.strip()
            ):

                self.add_error(
                    'designation',
                    'Designation is required.'
                )

            if (
                not work_location
                or not work_location.strip()
            ):

                self.add_error(
                    'work_location',
                    'Work location is required.'
                )

            if (
                not work_shift
                or not work_shift.strip()
            ):

                self.add_error(
                    'work_shift',
                    'Work shift is required.'
                )

        return cleaned_data

    # ========================================================
    # PASSWORD VALIDATION
    # ========================================================

    def clean_password2(self):

        password1 = self.cleaned_data.get(
            'password1'
        )

        password2 = self.cleaned_data.get(
            'password2'
        )

        if password1 and password2:

            if password1 != password2:

                raise forms.ValidationError(
                    "Passwords do not match."
                )

            if len(password1) < 8:

                raise forms.ValidationError(
                    "Password must be at least 8 characters."
                )

        return password2