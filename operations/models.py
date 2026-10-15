"""
Database models for Factory Operations & Quality Control System.
All 4 core features are supported:
1. UserProfile: Role management (Admin, Inspector, Supervisor).
2. ProductionJob: Tracks manufacturing jobs and dispatch clearance status.
3. Inspection: Measurement recording, auto PASS/FAIL calculation, supervisor review.
4. DefectPhoto: Image attachments for out-of-tolerance (FAIL) inspections.
5. ProcessHold: Production holds that block dispatch clearance until resolved.
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends standard Django User model to store roles.
    Roles:
      - ADMIN: Full access, user management, system oversight.
      - INSPECTOR: Creates measurements, submits inspections, attaches defect photos.
      - SUPERVISOR: Reviews inspections (Approve/Reject/Return), clears dispatch.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('INSPECTOR', 'Inspector'),
        ('SUPERVISOR', 'Supervisor'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='INSPECTOR')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.user.is_superuser

    @property
    def is_inspector(self):
        return self.role == 'INSPECTOR'

    @property
    def is_supervisor(self):
        return self.role == 'SUPERVISOR'


# Automatically create or update UserProfile whenever a User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Superuser defaults to ADMIN role
        initial_role = 'ADMIN' if instance.is_superuser else 'INSPECTOR'
        UserProfile.objects.create(user=instance, role=initial_role)
    else:
        # Ensure profile exists if user was created before signal
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            initial_role = 'ADMIN' if instance.is_superuser else 'INSPECTOR'
            UserProfile.objects.create(user=instance, role=initial_role)


class ProductionJob(models.Model):
    """
    Represents a manufacturing production order/batch.
    Contains product details and dispatch clearance status.
    """
    DISPATCH_STATUS_CHOICES = [
        ('PENDING', 'Pending Clearance'),
        ('CLEARED', 'Cleared for Dispatch'),
    ]

    job_number = models.CharField(max_length=50, unique=True, help_text="Unique Job or Batch Number (e.g., JOB-2026-001)")
    product_name = models.CharField(max_length=150, help_text="Name of the product (e.g., Steel Flange 50mm)")
    target_quantity = models.PositiveIntegerField(default=100, help_text="Total units to produce")
    created_at = models.DateTimeField(auto_now_add=True)

    # Dispatch tracking
    dispatch_status = models.CharField(max_length=20, choices=DISPATCH_STATUS_CHOICES, default='PENDING')
    cleared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cleared_jobs')
    cleared_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job_number} - {self.product_name}"

    def get_suggested_parameters(self):
        """
        Returns relevant metrology parameters based on the product type.
        Ensures product description and inspection measurements are genuinely consistent.
        """
        name = (self.product_name or "").lower()
        if any(k in name for k in ['chair', 'table', 'desk', 'furniture', 'wood', 'bench']):
            return [
                {"name": "Leg Height (H)", "min": 440.000, "max": 450.000, "desc": "Floor to seat base height"},
                {"name": "Seat Width (W)", "min": 445.000, "max": 455.000, "desc": "Side-to-side seating clearance"},
                {"name": "Backrest Height", "min": 820.000, "max": 840.000, "desc": "Overall vertical backrest dimension"},
                {"name": "Frame Squareness", "min": 0.000, "max": 2.000, "desc": "Diagonal assembly tolerance"},
            ]
        elif any(k in name for k in ['flange', 'pipe', 'fitting']):
            return [
                {"name": "Outer Diameter (OD)", "min": 49.800, "max": 50.200, "desc": "External machined diameter"},
                {"name": "Bore Inner Diameter (ID)", "min": 25.000, "max": 25.150, "desc": "Center pass-through bore"},
                {"name": "Flange Thickness (T)", "min": 12.000, "max": 12.400, "desc": "Mating flange thickness"},
                {"name": "Bolt Circle Diameter (BCD)", "min": 75.000, "max": 75.500, "desc": "Mounting bolt hole center circle"},
            ]
        elif any(k in name for k in ['valve', 'body', 'manifold']):
            return [
                {"name": "Port Diameter (ID)", "min": 30.000, "max": 30.200, "desc": "Fluid channel inner port diameter"},
                {"name": "Flange Face Flatness", "min": 0.000, "max": 0.050, "desc": "Precision sealing surface flatness"},
                {"name": "Wall Thickness (T)", "min": 10.000, "max": 10.500, "desc": "Pressure boundary wall thickness"},
            ]
        elif any(k in name for k in ['bearing', 'housing', 'turbine']):
            return [
                {"name": "Bore Inner Diameter (ID)", "min": 119.900, "max": 120.100, "desc": "Journal bearing sleeve bore"},
                {"name": "Housing Outer Diameter (OD)", "min": 150.000, "max": 150.250, "desc": "Outer mount fit diameter"},
                {"name": "Radial Runout", "min": 0.000, "max": 0.025, "desc": "Dynamic concentricity limit"},
            ]
        elif any(k in name for k in ['piston', 'shaft', 'rod', 'cylinder']):
            return [
                {"name": "Shaft Length (L)", "min": 150.000, "max": 150.300, "desc": "Overall shaft length"},
                {"name": "Outer Diameter (OD)", "min": 29.950, "max": 30.020, "desc": "Precision sliding diameter"},
                {"name": "Surface Finish (Ra)", "min": 0.200, "max": 0.800, "desc": "Roughness average limit"},
            ]
        return [
            {"name": "Critical Dimension (A)", "min": 49.500, "max": 50.500, "desc": "Primary manufacturing specification"},
            {"name": "Length / Height", "min": 99.000, "max": 101.000, "desc": "Overall longitudinal dimension"},
            {"name": "Thickness / Depth", "min": 9.500, "max": 10.500, "desc": "Sectional thickness"},
        ]

    def get_dispatch_block_reasons(self):
        """
        Validates all business rules required for dispatch clearance:
        Rule 1: At least one inspection must be recorded.
        Rule 2: Every inspection must be APPROVED by a supervisor.
        Rule 3: No inspections can be in PENDING, REJECTED, or RETURNED status.
        Rule 4: All active process holds must be released before dispatch.
        
        Returns a list of strings explaining why dispatch is blocked.
        If the list is empty, dispatch clearance is permitted.
        """
        reasons = []

        # Check inspections count
        inspections = self.inspections.all()
        if not inspections.exists():
            reasons.append("No quality inspection has been recorded for this job.")
        else:
            # Check for non-approved inspections
            unapproved = inspections.exclude(status='APPROVED')
            if unapproved.exists():
                pending_count = unapproved.filter(status='PENDING').count()
                rejected_count = unapproved.filter(status='REJECTED').count()
                returned_count = unapproved.filter(status='RETURNED').count()

                details = []
                if pending_count > 0:
                    details.append(f"{pending_count} pending review")
                if rejected_count > 0:
                    details.append(f"{rejected_count} rejected")
                if returned_count > 0:
                    details.append(f"{returned_count} returned for correction")

                reasons.append(f"Not all inspections are approved ({', '.join(details)}). Final supervisor approval is mandatory.")

        # Check for active process holds
        active_holds = self.process_holds.filter(is_active=True)
        if active_holds.exists():
            hold_reasons = [h.reason for h in active_holds]
            reasons.append(f"Active process hold in place: {'; '.join(hold_reasons)}. Hold must be released first.")

        return reasons

    @property
    def can_clear_dispatch(self):
        """Helper property: True if 0 blocking reasons exist and not yet cleared."""
        return len(self.get_dispatch_block_reasons()) == 0 and self.dispatch_status != 'CLEARED'


class Inspection(models.Model):
    """
    Represents a quality check recorded by an Inspector.
    Includes measurement, limits, auto-calculated result, and supervisor review.
    """
    RESULT_CHOICES = [
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Supervisor Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RETURNED', 'Returned for Correction'),
    ]

    job = models.ForeignKey(ProductionJob, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inspections_created')
    
    # Measurement parameters
    sample_unit_number = models.PositiveIntegerField(default=1, help_text="Sample piece / unit identifier (e.g. Unit #1)")
    parameter_name = models.CharField(max_length=100, default="Critical Dimension", help_text="e.g. Outer Diameter, Thickness, Length")
    measurement = models.DecimalField(max_digits=10, decimal_places=3, help_text="Actual measured value")
    min_limit = models.DecimalField(max_digits=10, decimal_places=3, help_text="Minimum acceptable tolerance limit")
    max_limit = models.DecimalField(max_digits=10, decimal_places=3, help_text="Maximum acceptable tolerance limit")

    # Auto-calculated result (PASS if min_limit <= measurement <= max_limit, else FAIL)
    calculated_result = models.CharField(max_length=10, choices=RESULT_CHOICES, editable=False)

    # Supervisor Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspections_reviewed')
    supervisor_comment = models.TextField(blank=True, null=True, help_text="Mandatory if rejected or returned")
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_result(self):
        """
        Calculates PASS or FAIL based on tolerance limits:
        PASS: min_limit <= measurement <= max_limit
        FAIL: measurement < min_limit OR measurement > max_limit
        """
        if self.min_limit is not None and self.max_limit is not None and self.measurement is not None:
            if Decimal(str(self.min_limit)) <= Decimal(str(self.measurement)) <= Decimal(str(self.max_limit)):
                return 'PASS'
        return 'FAIL'

    def save(self, *args, **kwargs):
        # Automatically calculate PASS or FAIL before saving to database
        self.calculated_result = self.calculate_result()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inspection #{self.id} for {self.job.job_number} - {self.calculated_result} ({self.status})"


class DefectPhoto(models.Model):
    """
    Defect photo uploaded for an out-of-tolerance (FAIL) inspection.
    Requirement: At least two defect photos required before submitting a FAIL inspection.
    """
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='defect_photos')
    image = models.ImageField(upload_to='defect_photos/', help_text="Upload photo showing defect/damage")
    caption = models.CharField(max_length=150, blank=True, help_text="Optional description of the defect")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo #{self.id} for Inspection #{self.inspection_id}"


class ProcessHold(models.Model):
    """
    Represents an operational or quality hold placed on a job.
    While active, blocks dispatch clearance.
    """
    job = models.ForeignKey(ProductionJob, on_delete=models.CASCADE, related_name='process_holds')
    reason = models.TextField(help_text="Detailed reason for placing the job on hold")
    is_active = models.BooleanField(default=True, help_text="Checked = Hold is active; Unchecked = Hold released")
    
    # Placed tracking
    placed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='placed_holds')
    placed_at = models.DateTimeField(auto_now_add=True)

    # Release tracking
    released_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='released_holds')
    released_at = models.DateTimeField(null=True, blank=True)
    release_notes = models.TextField(blank=True, null=True, help_text="Explanation of how the issue was resolved")

    def release(self, user, notes=""):
        """Releases the hold."""
        self.is_active = False
        self.released_by = user
        self.released_at = timezone.now()
        self.release_notes = notes
        self.save()

    def __str__(self):
        status_text = "ACTIVE" if self.is_active else "RELEASED"
        return f"Hold #{self.id} on {self.job.job_number} [{status_text}]: {self.reason[:40]}"


class QualityCertificate(models.Model):
    """
    Persisted Certificate of Quality & Dispatch Release.
    Stores the official certificate reference, generation timestamp, cryptographic hash,
    sample coverage metrics, and the related production job in the database.
    """
    job = models.ForeignKey(ProductionJob, on_delete=models.CASCADE, related_name='certificates')
    certificate_number = models.CharField(max_length=100, unique=True, help_text="Official Certificate Reference Number")
    generated_at = models.DateTimeField(default=timezone.now, help_text="Timestamp of certificate generation (UTC)")
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates_generated')
    
    # Clearance and verification authorization
    is_dispatch_authorized = models.BooleanField(
        default=False,
        help_text="True strictly when all inspections are approved, 0 active holds, and job is officially cleared"
    )
    sha256_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Cryptographic SHA-256 verification digest of certificate payload"
    )

    # Audited sampling and statistics at generation time
    total_inspections = models.PositiveIntegerField(default=0)
    passed_inspections = models.PositiveIntegerField(default=0)
    failed_inspections = models.PositiveIntegerField(default=0)
    inspected_units_count = models.PositiveIntegerField(default=1, help_text="Actual count of distinct sampled units")
    inspected_dimensions_count = models.PositiveIntegerField(default=1, help_text="Actual count of critical dimensions checked")
    first_pass_yield = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Calculated FPY %")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        auth_status = "AUTHORIZED" if self.is_dispatch_authorized else "PROVISIONAL"
        return f"{self.certificate_number} - {self.job.job_number} [{auth_status}]"

