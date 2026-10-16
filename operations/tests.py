from decimal import Decimal
import io
from PIL import Image
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from operations.models import ProductionJob, Inspection, ProcessHold, DefectPhoto, UserProfile, QualityCertificate
from operations.forms import InspectionCreateForm, SupervisorReviewForm


def create_test_image(name='test.jpg'):
    """Helper to generate an in-memory JPEG file for upload tests."""
    file_obj = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file_obj, 'jpeg')
    file_obj.seek(0)
    return SimpleUploadedFile(name, file_obj.read(), content_type='image/jpeg')


class QualiTrackFeatureTests(TestCase):
    def setUp(self):
        # 1. Create Test Users
        self.admin_user = User.objects.create_superuser(
            username='test_admin', password='password123', email='admin@test.com'
        )
        self.admin_user.profile.role = 'ADMIN'
        self.admin_user.profile.save()

        self.inspector_user = User.objects.create_user(
            username='test_inspector', password='password123', email='inspector@test.com'
        )
        self.inspector_user.profile.role = 'INSPECTOR'
        self.inspector_user.profile.save()

        self.supervisor_user = User.objects.create_user(
            username='test_supervisor', password='password123', email='supervisor@test.com'
        )
        self.supervisor_user.profile.role = 'SUPERVISOR'
        self.supervisor_user.profile.save()

        # 2. Create Sample Production Job
        self.job = ProductionJob.objects.create(
            job_number='JOB-TEST-001',
            product_name='Titanium Rotor Flange',
            target_quantity=100
        )

        self.client = Client()

    # --------------------------------------------------------------------------
    # FEATURE 1: Authentication & Role-Based Access Tests
    # --------------------------------------------------------------------------
    def test_login_role_mismatch_prevented(self):
        """Test that an inspector cannot log in selecting the ADMIN role."""
        response = self.client.post(reverse('login'), {
            'username': 'test_inspector',
            'password': 'password123',
            'role': 'ADMIN'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Role Mismatch")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_successful_redirects_to_correct_dashboard(self):
        """Test inspector logs in and gets redirected to inspector dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'test_inspector',
            'password': 'password123',
            'role': 'INSPECTOR'
        })
        self.assertRedirects(response, reverse('inspector_dashboard'))

    def test_role_required_decorator_blocks_unauthorized_role(self):
        """Test that an inspector attempting to access supervisor dashboard is redirected to their own dashboard."""
        self.client.login(username='test_inspector', password='password123')
        response = self.client.get(reverse('supervisor_dashboard'))
        self.assertRedirects(response, reverse('inspector_dashboard'))

    def test_home_page_renders_successfully(self):
        """Test that the public home page renders 200 OK with metrics and role links."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QualiTrack")
        self.assertContains(response, "Enter Factory Portal")
        self.assertContains(response, "INSPECTOR")
        self.assertContains(response, "SUPERVISOR")
        self.assertContains(response, "ADMIN")

    def test_home_page_redirects_authenticated_user(self):
        """Test that an authenticated user visiting home is redirected to dashboard redirect."""
        self.client.login(username='test_inspector', password='password123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard_redirect'))

    # --------------------------------------------------------------------------
    # FEATURE 2: Inspection Management & PASS/FAIL Calculation Tests
    # --------------------------------------------------------------------------
    def test_auto_pass_calculation(self):
        """Measurement within tolerance automatically receives PASS result."""
        inspection = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Outer Diameter',
            min_limit=Decimal('49.500'),
            max_limit=Decimal('50.500'),
            measurement=Decimal('50.025')
        )
        self.assertEqual(inspection.calculated_result, 'PASS')
        self.assertEqual(inspection.status, 'PENDING')

    def test_auto_fail_calculation(self):
        """Measurement outside tolerance automatically receives FAIL result."""
        inspection = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Outer Diameter',
            min_limit=Decimal('49.500'),
            max_limit=Decimal('50.500'),
            measurement=Decimal('51.200')
        )
        self.assertEqual(inspection.calculated_result, 'FAIL')

    def test_fail_inspection_requires_at_least_two_defect_photos(self):
        """Validation fails if an out-of-tolerance inspection is submitted with fewer than 2 photos."""
        self.client.login(username='test_inspector', password='password123')

        # Attempt with only 1 photo
        img1 = create_test_image('defect1.jpg')
        response = self.client.post(reverse('inspection_create'), {
            'job': self.job.id,
            'parameter_name': 'Outer Diameter',
            'min_limit': '49.500',
            'max_limit': '50.500',
            'measurement': '51.800',  # FAIL
            'defect_photos': [img1],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "REQUIRES at least TWO (2) defect photos")
        self.assertEqual(Inspection.objects.count(), 0)

    def test_fail_inspection_succeeds_with_two_defect_photos(self):
        """Submission succeeds when 2 defect photos are uploaded for a FAIL inspection."""
        self.client.login(username='test_inspector', password='password123')

        img1 = create_test_image('defect1.jpg')
        img2 = create_test_image('defect2.jpg')
        response = self.client.post(reverse('inspection_create'), {
            'job': self.job.id,
            'parameter_name': 'Outer Diameter',
            'min_limit': '49.500',
            'max_limit': '50.500',
            'measurement': '51.800',  # FAIL
            'defect_photos': [img1, img2],
            'photo_caption': 'Major dimensional out-of-tolerance burr',
        })
        self.assertEqual(Inspection.objects.count(), 1)
        insp = Inspection.objects.first()
        self.assertEqual(insp.calculated_result, 'FAIL')
        self.assertEqual(insp.defect_photos.count(), 2)

    def test_pass_inspection_succeeds_without_photos(self):
        """Submission succeeds without photos when the measurement passes tolerance."""
        self.client.login(username='test_inspector', password='password123')
        response = self.client.post(reverse('inspection_create'), {
            'job': self.job.id,
            'parameter_name': 'Outer Diameter',
            'min_limit': '49.500',
            'max_limit': '50.500',
            'measurement': '50.150',  # PASS
        })
        self.assertEqual(Inspection.objects.count(), 1)
        insp = Inspection.objects.first()
        self.assertEqual(insp.calculated_result, 'PASS')
        self.assertRedirects(response, reverse('inspection_detail', kwargs={'pk': insp.id}))

    # --------------------------------------------------------------------------
    # FEATURE 3: Supervisor Review & Anti Self-Approval Tests
    # --------------------------------------------------------------------------
    def test_supervisor_can_approve_inspection(self):
        """Supervisor can review and approve a pending inspection."""
        insp = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Thickness',
            min_limit=Decimal('10.000'),
            max_limit=Decimal('10.500'),
            measurement=Decimal('10.250')
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.post(reverse('inspection_review', kwargs={'pk': insp.id}), {
            'decision': 'APPROVED',
            'supervisor_comment': 'Verified within tolerances.'
        })
        self.assertRedirects(response, reverse('supervisor_dashboard'))
        insp.refresh_from_db()
        self.assertEqual(insp.status, 'APPROVED')
        self.assertEqual(insp.supervisor, self.supervisor_user)

    def test_supervisor_rejection_requires_comment(self):
        """Supervisor rejecting an inspection without remarks is rejected by form validation."""
        insp = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Thickness',
            min_limit=Decimal('10.000'),
            max_limit=Decimal('10.500'),
            measurement=Decimal('11.000')
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.post(reverse('inspection_review', kwargs={'pk': insp.id}), {
            'decision': 'REJECTED',
            'supervisor_comment': ''  # Empty remark
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "remarks are strictly required")
        insp.refresh_from_db()
        self.assertEqual(insp.status, 'PENDING')

    def test_anti_self_approval_protection(self):
        """An inspector cannot review or approve their own inspection."""
        insp = Inspection.objects.create(
            job=self.job,
            inspector=self.supervisor_user,  # Created by supervisor themselves
            parameter_name='Thickness',
            min_limit=Decimal('10.000'),
            max_limit=Decimal('10.500'),
            measurement=Decimal('10.250')
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('inspection_review', kwargs={'pk': insp.id}))
        self.assertRedirects(response, reverse('supervisor_dashboard'))
        insp.refresh_from_db()
        self.assertEqual(insp.status, 'PENDING')

    # --------------------------------------------------------------------------
    # FEATURE 4: Dispatch Clearance & Process Holds Tests
    # --------------------------------------------------------------------------
    def test_dispatch_blocked_if_no_inspections(self):
        """Rule 1: Job without any inspections is blocked from dispatch clearance."""
        reasons = self.job.get_dispatch_block_reasons()
        self.assertTrue(any("No quality inspection has been recorded" in r for r in reasons))
        self.assertFalse(self.job.can_clear_dispatch)

    def test_dispatch_blocked_if_inspections_unapproved(self):
        """Rule 2 & 3: Job with pending or rejected inspections is blocked."""
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Diameter',
            min_limit=Decimal('50.000'),
            max_limit=Decimal('50.200'),
            measurement=Decimal('50.100'),
            status='PENDING'
        )
        reasons = self.job.get_dispatch_block_reasons()
        self.assertTrue(any("Not all inspections are approved" in r for r in reasons))
        self.assertFalse(self.job.can_clear_dispatch)

    def test_dispatch_blocked_by_active_process_hold(self):
        """Rule 4: Active process hold blocks dispatch clearance even if inspection is approved."""
        insp = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Diameter',
            min_limit=Decimal('50.000'),
            max_limit=Decimal('50.200'),
            measurement=Decimal('50.100'),
            status='APPROVED'
        )
        hold = ProcessHold.objects.create(
            job=self.job,
            reason='CNC spindle recalibration audit',
            placed_by=self.supervisor_user,
            is_active=True
        )
        reasons = self.job.get_dispatch_block_reasons()
        self.assertTrue(any("Active process hold in place" in r for r in reasons))
        self.assertFalse(self.job.can_clear_dispatch)

        # Release the hold
        hold.release(user=self.supervisor_user, notes='Spindle recalibrated and certified.')
        self.job.refresh_from_db()
        self.assertEqual(len(self.job.get_dispatch_block_reasons()), 0)
        self.assertTrue(self.job.can_clear_dispatch)

    def test_dispatch_clearance_execution(self):
        """Official dispatch clearance succeeds when all 4 rules are met."""
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Diameter',
            min_limit=Decimal('50.000'),
            max_limit=Decimal('50.200'),
            measurement=Decimal('50.100'),
            status='APPROVED'
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.post(reverse('clear_dispatch', kwargs={'pk': self.job.id}))
        self.assertRedirects(response, reverse('job_detail', kwargs={'pk': self.job.id}))
        
        self.job.refresh_from_db()
        self.assertEqual(self.job.dispatch_status, 'CLEARED')
        self.assertEqual(self.job.cleared_by, self.supervisor_user)
        self.assertIsNotNone(self.job.cleared_at)

    # --------------------------------------------------------------------------
    # ENTERPRISE EXTENSIONS: Certificate (COA) & CSV Data Export Tests
    # --------------------------------------------------------------------------
    def test_job_certificate_view(self):
        """Official certificate of analysis view renders with Quality metadata and batch info."""
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certificate of Quality")
        self.assertContains(response, self.job.job_number)

    def test_certificate_timestamps_explicit_timezone(self):
        """Requirement 1: Valid timestamps with explicit UTC timezone and no malformed date strings."""
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Explicit UTC timezone displayed
        self.assertIn("UTC", content)
        # Malformed template formatting characters like '&oct' or '&Wednesday' must not exist
        self.assertNotIn("&bull; H:i", content)
        self.assertNotIn("&oct", content)

    def test_certificate_measurement_lsl_usl_pass_fail(self):
        """Requirement 4: PASS only when measurement is strictly within [LSL, USL]."""
        # Create 1 pass and 1 fail inspection
        insp_pass = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Outer Diameter',
            min_limit=Decimal('49.500'),
            max_limit=Decimal('50.500'),
            measurement=Decimal('50.000'),
            status='APPROVED',
        )
        insp_fail = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Bore Depth',
            min_limit=Decimal('10.000'),
            max_limit=Decimal('11.000'),
            measurement=Decimal('12.500'),
            status='APPROVED',
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("PASS", content)
        self.assertIn("FAIL", content)
        self.assertIn("49.500 mm", content)
        self.assertIn("50.500 mm", content)
        self.assertIn("12.500 mm", content)

    def test_certificate_yield_calculated_not_hardcoded(self):
        """Requirement 5: First-pass yield calculated from actual recorded data, never hard-coded 100%."""
        # 1 PASS, 1 FAIL = 50.0% yield
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Flange OD',
            min_limit=Decimal('49.000'),
            max_limit=Decimal('51.000'),
            measurement=Decimal('50.000'),
            status='APPROVED',
        )
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Flange ID',
            min_limit=Decimal('20.000'),
            max_limit=Decimal('21.000'),
            measurement=Decimal('25.000'),
            status='APPROVED',
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['quality_yield'], Decimal('50.0'))
        self.assertContains(response, "50.0% Pass Rate")

    def test_certificate_sampling_scope_distinguishes_units(self):
        """Requirement 6: Shows actual sampled units and critical dimensions, does not imply 1 inspection verifies all 100 units."""
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            sample_unit_number=1,
            parameter_name='Diameter',
            min_limit=Decimal('49.000'),
            max_limit=Decimal('51.000'),
            measurement=Decimal('50.000'),
            status='APPROVED',
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100 units produced")
        self.assertContains(response, "1 sample unit(s)")
        self.assertContains(response, "Sampling Scope")

    def test_certificate_unverified_iso_claim_omitted(self):
        """Requirement 7: Do not claim ISO certification unless verified."""
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Must not falsely claim ISO 9001:2015 Certified
        self.assertNotIn("ISO 9001:2015 Certified", content)
        self.assertContains(response, "QualiTrack Precision Metrology Standard")

    def test_certificate_genuine_sha256_hash(self):
        """Requirement 8: Real SHA-256 digest generated and stored, no fake hash."""
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Diameter',
            min_limit=Decimal('49.000'),
            max_limit=Decimal('51.000'),
            measurement=Decimal('50.000'),
            status='APPROVED',
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # No fake template hash string
        self.assertNotIn("SHA256-CERT-OK", content)
        # Real 64-character hexadecimal SHA-256 hash
        cert = QualityCertificate.objects.get(job=self.job)
        self.assertEqual(len(cert.sha256_hash), 64)
        self.assertIn(cert.sha256_hash, content)

    def test_certificate_backend_dispatch_verification(self):
        """Requirement 9: Authorized certificate only after all inspections approved and 0 holds verified on backend."""
        # Step A: Incomplete job with pending inspection -> Provisional status
        insp = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Diameter',
            min_limit=Decimal('49.000'),
            max_limit=Decimal('51.000'),
            measurement=Decimal('50.000'),
            status='PENDING',
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_dispatch_authorized'])
        self.assertContains(response, "PROVISIONAL")

        # Step B: Approve inspection and officially clear dispatch on backend
        insp.status = 'APPROVED'
        insp.supervisor = self.supervisor_user
        insp.save()
        clear_resp = self.client.post(reverse('clear_dispatch', kwargs={'pk': self.job.id}))
        self.assertEqual(clear_resp.status_code, 302)

        # Step C: Certificate is now authorized on backend
        response_auth = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertTrue(response_auth.context['is_dispatch_authorized'])
        self.assertContains(response_auth, "DISPATCH AUTHORIZED")
        self.assertContains(response_auth, "OFFICIAL QA RELEASE")

    def test_certificate_stored_in_database(self):
        """Requirement 10: Store certificate reference, generation timestamp, and production job in database."""
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}))
        self.assertEqual(response.status_code, 200)
        cert_exists = QualityCertificate.objects.filter(job=self.job).exists()
        self.assertTrue(cert_exists)
        cert = QualityCertificate.objects.get(job=self.job)
        self.assertTrue(cert.certificate_number.startswith("COA-"))
        self.assertIsNotNone(cert.generated_at)

    def test_certificate_pdf_binary_export(self):
        """PDF generation via ReportLab produces binary PDF stream with genuine SHA-256 hash."""
        Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Diameter',
            min_limit=Decimal('49.000'),
            max_limit=Decimal('51.000'),
            measurement=Decimal('50.000'),
            status='APPROVED',
        )
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('job_certificate', kwargs={'pk': self.job.id}) + '?format=pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertTrue('X-Certificate-SHA256' in response)
        self.assertEqual(len(response['X-Certificate-SHA256']), 64)

    def test_product_parameter_consistency(self):
        """Requirement 3: Product-appropriate inspection parameters (e.g. chairs have leg/seat dimensions, not shafts)."""
        chair_job = ProductionJob.objects.create(
            job_number='JOB-CHAIR-001',
            product_name='Executive Wooden Chair',
            target_quantity=50
        )
        flange_job = ProductionJob.objects.create(
            job_number='JOB-FLANGE-001',
            product_name='Precision Steel Flange 50mm',
            target_quantity=200
        )
        chair_params = [p['name'] for p in chair_job.get_suggested_parameters()]
        flange_params = [p['name'] for p in flange_job.get_suggested_parameters()]

        # Chair has leg height and seat width, NOT shaft length or bore diameter
        self.assertIn("Leg Height (H)", chair_params)
        self.assertIn("Seat Width (W)", chair_params)
        self.assertNotIn("Shaft Length (L)", chair_params)
        self.assertNotIn("Bore Inner Diameter (ID)", chair_params)

        # Flange has outer diameter and bolt circle diameter, NOT leg height
        self.assertIn("Outer Diameter (OD)", flange_params)
        self.assertNotIn("Leg Height (H)", flange_params)


    def test_export_inspections_csv(self):
        """CSV export of inspections returns valid spreadsheet headers and text/csv mime type."""
        self.client.login(username='test_inspector', password='password123')
        response = self.client.get(reverse('export_inspections_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Inspection_ID,Job_Number', response.content.decode('utf-8'))

    def test_export_jobs_csv(self):
        """CSV export of production batches returns valid spreadsheet data."""
        self.client.login(username='test_supervisor', password='password123')
        response = self.client.get(reverse('export_jobs_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Job_Number,Product_Name', response.content.decode('utf-8'))

    def test_login_redirects_to_next_url(self):
        """Test that login safely redirects to next parameter when provided."""
        next_target = reverse('inspection_create')
        response = self.client.post(reverse('login'), {
            'username': 'test_inspector',
            'password': 'password123',
            'role': 'INSPECTOR',
            'next': next_target,
        })
        self.assertRedirects(response, next_target)

    def test_inspection_form_orders_pending_batches_first(self):
        """Test that InspectionCreateForm orders PENDING batches before CLEARED batches."""
        cleared_job = ProductionJob.objects.create(
            job_number='JOB-CLEARED-099',
            product_name='Cleared Batch',
            dispatch_status='CLEARED'
        )
        form = InspectionCreateForm()
        jobs_list = list(form.fields['job'].queryset)
        # Find index of pending vs cleared job
        pending_idx = next(i for i, j in enumerate(jobs_list) if j.dispatch_status == 'PENDING')
        cleared_idx = next(i for i, j in enumerate(jobs_list) if j.id == cleared_job.id)
        self.assertLess(pending_idx, cleared_idx)

    def test_inspection_detail_context_has_calculated_result(self):
        """Test that inspection detail view passes calculated_result in context for template styling."""
        insp = Inspection.objects.create(
            job=self.job,
            inspector=self.inspector_user,
            parameter_name='Thickness',
            min_limit=Decimal('10.000'),
            max_limit=Decimal('10.500'),
            measurement=Decimal('10.250'),
        )
        self.client.login(username='test_inspector', password='password123')
        response = self.client.get(reverse('inspection_detail', kwargs={'pk': insp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['calculated_result'], 'PASS')

