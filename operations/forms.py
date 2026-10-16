"""
Forms for Factory Quality & Dispatch Management (QualiTrack).
Covers all 4 core features:
1. LoginForm: Role-based authentication and role mismatch prevention.
2. InspectionCreateForm: Quality measurement recording, auto PASS/FAIL check, and mandatory 2 defect photos validation for FAIL.
3. SupervisorReviewForm: Review decisions (Approve, Reject, Return) with mandatory comments for non-approvals.
4. ProcessHoldForm: Placing process holds on jobs.
5. ReleaseHoldForm: Releasing process holds with required resolution notes.
6. ProductionJobForm: Creating new production jobs/batches.
"""

from decimal import Decimal
from django import forms
from django.contrib.auth import authenticate
from .models import UserProfile, ProductionJob, Inspection, ProcessHold, DefectPhoto


class LoginForm(forms.Form):
    """
    Role-based Login Form.
    Factory users must explicitly select their operational role (Inspector, Supervisor, Admin).
    Authentication verifies credentials AND ensures the user cannot impersonate another role.
    """
    ROLE_CHOICES = [
        ('INSPECTOR', 'Inspector (Quality Checks & Measurements)'),
        ('SUPERVISOR', 'Supervisor (Approvals & Dispatch Clearance)'),
        ('ADMIN', 'Admin (System Oversight & User Management)'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        initial='INSPECTOR',
        help_text="Select your factory role to access your dedicated dashboard."
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # 1. Authenticate credentials
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password. Please check your credentials.")

            if not user.is_active:
                raise forms.ValidationError("This account has been disabled. Please contact your factory admin.")

            # 2. Verify selected role against database profile
            profile = getattr(user, 'profile', None)
            user_db_role = profile.role if profile else ('ADMIN' if user.is_superuser else None)

            # Allow superusers to log in as ADMIN
            is_valid_admin = user.is_superuser and role == 'ADMIN'

            if user_db_role != role and not is_valid_admin:
                role_dict = dict(UserProfile.ROLE_CHOICES)
                selected_label = role_dict.get(role, role)
                actual_label = role_dict.get(user_db_role, user_db_role or "None")
                raise forms.ValidationError(
                    f"Role Mismatch: You selected '{selected_label}', but your assigned account role is '{actual_label}'. "
                    f"Please select the '{actual_label}' tab to proceed."
                )

            # Store authenticated user for view to log in
            self.user = user

        return cleaned_data


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'defect_photos_input'
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class InspectionCreateForm(forms.ModelForm):
    """
    Form for Inspectors to record a quality inspection.
    Enforces tolerance rule calculation and requires at least 2 defect photos on FAIL.
    """
    defect_photos = MultipleFileField(
        required=False,
        help_text="Upload at least 2 photos if the inspection fails tolerance limits."
    )
    photo_caption = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of the defect observed (optional)'
        })
    )

    class Meta:
        model = Inspection
        fields = ['job', 'sample_unit_number', 'parameter_name', 'min_limit', 'max_limit', 'measurement']
        widgets = {
            'job': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'job_select'}),
            'sample_unit_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1',
                'id': 'sample_unit_number'
            }),
            'parameter_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Outer Diameter, Thickness, Leg Height',
                'id': 'parameter_name'
            }),
            'min_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'e.g. 49.500',
                'id': 'min_limit'
            }),
            'max_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'e.g. 50.500',
                'id': 'max_limit'
            }),
            'measurement': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg fw-bold',
                'step': '0.001',
                'placeholder': 'e.g. 50.120',
                'id': 'measurement'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'sample_unit_number' in self.fields:
            self.fields['sample_unit_number'].required = False
            self.fields['sample_unit_number'].initial = 1
        # Display jobs that are pending clearance first ('PENDING' before 'CLEARED')
        self.fields['job'].queryset = ProductionJob.objects.all().order_by('-dispatch_status', '-created_at')

    def clean_sample_unit_number(self):
        val = self.cleaned_data.get('sample_unit_number')
        return val if val is not None and val > 0 else 1

    def clean(self):
        cleaned_data = super().clean()
        min_limit = cleaned_data.get('min_limit')
        max_limit = cleaned_data.get('max_limit')
        measurement = cleaned_data.get('measurement')

        if min_limit is not None and max_limit is not None:
            if Decimal(str(min_limit)) > Decimal(str(max_limit)):
                raise forms.ValidationError("Minimum tolerance limit cannot be greater than Maximum tolerance limit.")

        if min_limit is not None and max_limit is not None and measurement is not None:
            min_val = Decimal(str(min_limit))
            max_val = Decimal(str(max_limit))
            meas_val = Decimal(str(measurement))

            # Rule check: PASS if min <= meas <= max
            is_pass = (min_val <= meas_val <= max_val)

            # Retrieve uploaded defect photos (can come from defect_photos multiple field or individual files)
            files = self.files.getlist('defect_photos') if hasattr(self, 'files') else []
            # Filter out empty entries if any
            valid_files = [f for f in files if f and getattr(f, 'size', 0) > 0]

            if not is_pass:
                # Must have at least 2 defect photos
                if len(valid_files) < 2:
                    raise forms.ValidationError(
                        f"Out-of-Tolerance (FAIL) Inspection Alert: Measured value {meas_val} is outside "
                        f"the acceptable range [{min_val} - {max_val}]. "
                        f"Company Quality Policy STRICTLY REQUIRES at least TWO (2) defect photos "
                        f"documenting the non-conformance before submission. (Uploaded: {len(valid_files)})."
                    )

        return cleaned_data


class SupervisorReviewForm(forms.Form):
    """
    Form for Supervisors to make an Approval decision on an inspection.
    Choices: APPROVED, REJECTED, RETURNED.
    Comments are mandatory for REJECTED and RETURNED.
    """
    DECISION_CHOICES = [
        ('APPROVED', 'Approve Inspection (Passes Quality Standard)'),
        ('REJECTED', 'Reject Inspection (Quality Defect Unacceptable)'),
        ('RETURNED', 'Return to Inspector for Re-measurement / Correction'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        initial='APPROVED',
        help_text="Select your supervisory decision for this quality inspection."
    )
    supervisor_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your evaluation remarks, corrective action instructions, or notes...'
        }),
        help_text="Mandatory if Rejecting or Returning the inspection."
    )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        comment = cleaned_data.get('supervisor_comment', '').strip()

        if decision in ['REJECTED', 'RETURNED'] and not comment:
            action_word = "rejecting" if decision == 'REJECTED' else "returning"
            raise forms.ValidationError(
                f"Supervisor remarks are strictly required when {action_word} an inspection. "
                f"Please explain the reason for the decision."
            )

        return cleaned_data


class ProcessHoldForm(forms.ModelForm):
    """
    Form to place an operational or quality hold on a job.
    """
    class Meta:
        model = ProcessHold
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detail the reason for halting dispatch (e.g., tooling recalibration, customer hold, defect rate investigation)...'
            })
        }


class ReleaseHoldForm(forms.Form):
    """
    Form to release an active process hold.
    """
    release_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe how the issue was resolved and why it is safe to resume production/dispatch...'
        }),
        help_text="Provide justification for releasing the hold."
    )

    def clean_release_notes(self):
        notes = self.cleaned_data.get('release_notes', '').strip()
        if not notes:
            raise forms.ValidationError("Release notes are required to document the resolution before releasing the hold.")
        return notes


class ProductionJobForm(forms.ModelForm):
    """
    Form to create or edit production orders.
    """
    class Meta:
        model = ProductionJob
        fields = ['job_number', 'product_name', 'target_quantity']
        widgets = {
            'job_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. JOB-2026-004'
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Stainless Steel Precision Shaft 25mm'
            }),
            'target_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 250'
            }),
        }
