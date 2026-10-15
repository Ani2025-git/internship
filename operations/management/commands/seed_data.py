"""
Django management command to seed initial users, production jobs, inspections,
defect photos, and process holds for testing and demonstration.
Usage:
    python manage.py seed_data
"""

from decimal import Decimal
import os
import io
from PIL import Image, ImageDraw, ImageFont
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings

from operations.models import UserProfile, ProductionJob, Inspection, ProcessHold, DefectPhoto


def generate_demo_defect_image(title="DEFECT SAMPLE", subtitle="Out of Tolerance"):
    """Creates a sample factory defect inspection photo with annotations."""
    img = Image.new('RGB', (640, 480), color=(40, 45, 55))
    draw = ImageDraw.Draw(img)

    # Grid lines to resemble optical measurement
    for x in range(0, 640, 40):
        draw.line([(x, 0), (x, 480)], fill=(60, 65, 75), width=1)
    for y in range(0, 480, 40):
        draw.line([(0, y), (640, y)], fill=(60, 65, 75), width=1)

    # Highlight circle for defect area
    draw.ellipse([260, 180, 380, 300], outline=(239, 68, 68), width=3)
    draw.line([(320, 160), (320, 320)], fill=(239, 68, 68), width=2)
    draw.line([(240, 240), (400, 240)], fill=(239, 68, 68), width=2)

    # Text banner
    draw.rectangle([20, 20, 400, 90], fill=(15, 23, 42))
    draw.text((30, 28), f"FACTORY QC OPTICAL INSPECTION", fill=(245, 158, 11))
    draw.text((30, 48), title, fill=(255, 255, 255))
    draw.text((30, 68), subtitle, fill=(239, 68, 68))

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Seeds initial demo users, jobs, inspections, defect photos, and process holds."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Factory QC demo data...")

        # 1. Admin
        admin_user, _ = User.objects.get_or_create(username="admin", defaults={
            "email": "admin@factoryqc.local",
            "first_name": "System",
            "last_name": "Admin",
            "is_staff": True,
            "is_superuser": True,
        })
        admin_user.set_password("admin123")
        admin_user.save()
        admin_user.profile.role = "ADMIN"
        admin_user.profile.save()
        self.stdout.write(self.style.SUCCESS("[OK] Admin: username='admin', password='admin123'"))

        # 2. Inspector
        inspector_user, _ = User.objects.get_or_create(username="inspector1", defaults={
            "email": "inspector1@factoryqc.local",
            "first_name": "Rahul",
            "last_name": "Sharma",
        })
        inspector_user.set_password("inspector123")
        inspector_user.save()
        inspector_user.profile.role = "INSPECTOR"
        inspector_user.profile.save()
        self.stdout.write(self.style.SUCCESS("[OK] Inspector: username='inspector1', password='inspector123'"))

        # 3. Supervisor
        supervisor_user, _ = User.objects.get_or_create(username="supervisor1", defaults={
            "email": "supervisor1@factoryqc.local",
            "first_name": "Priya",
            "last_name": "Patel",
        })
        supervisor_user.set_password("supervisor123")
        supervisor_user.save()
        supervisor_user.profile.role = "SUPERVISOR"
        supervisor_user.profile.save()
        self.stdout.write(self.style.SUCCESS("[OK] Supervisor: username='supervisor1', password='supervisor123'"))

        # 4. Production Jobs
        job1, _ = ProductionJob.objects.get_or_create(
            job_number="JOB-2026-001",
            defaults={"product_name": "Precision Steel Flange 50mm", "target_quantity": 200}
        )
        job2, _ = ProductionJob.objects.get_or_create(
            job_number="JOB-2026-002",
            defaults={"product_name": "Alloy Hydraulic Valve Body", "target_quantity": 150}
        )
        job3, _ = ProductionJob.objects.get_or_create(
            job_number="JOB-2026-003",
            defaults={"product_name": "Turbine Bearing Housing 120mm", "target_quantity": 80}
        )
        job4, _ = ProductionJob.objects.get_or_create(
            job_number="JOB-2026-004",
            defaults={"product_name": "High-Pressure Hydraulic Piston 30mm", "target_quantity": 300}
        )

        # 5. Job 1: Add Approved PASS Inspection -> Makes it Ready for Dispatch!
        insp1, created1 = Inspection.objects.get_or_create(
            job=job1,
            parameter_name="Outer Diameter (OD)",
            defaults={
                "inspector": inspector_user,
                "min_limit": Decimal("49.800"),
                "max_limit": Decimal("50.200"),
                "measurement": Decimal("50.050"),
                "status": "APPROVED",
                "supervisor": supervisor_user,
                "supervisor_comment": "Dimensional tolerance verified with calibrated vernier caliper.",
                "reviewed_at": timezone.now(),
            }
        )
        if created1:
            self.stdout.write(self.style.SUCCESS(f"  + Created Approved Inspection #{insp1.id} for {job1.job_number} (READY FOR DISPATCH)"))

        # 6. Job 2: Add Active Process Hold -> Demonstrates Hold Blocking Rule!
        hold2, created_hold = ProcessHold.objects.get_or_create(
            job=job2,
            reason="Tooling recalibration required on CNC Machine #3 due to chatter marks.",
            defaults={
                "placed_by": supervisor_user,
                "is_active": True,
            }
        )
        if created_hold:
            self.stdout.write(self.style.WARNING(f"  + Placed Active Process Hold on {job2.job_number} (BLOCKED BY HOLD)"))

        # 7. Job 3: Add Pending FAIL Inspection with 2 Defect Photos -> Demonstrates Supervisor Review & Defect Photos!
        insp3, created3 = Inspection.objects.get_or_create(
            job=job3,
            parameter_name="Bore Inner Diameter (ID)",
            defaults={
                "inspector": inspector_user,
                "min_limit": Decimal("119.900"),
                "max_limit": Decimal("120.100"),
                "measurement": Decimal("120.350"), # FAIL: 0.25mm oversize
                "status": "PENDING",
            }
        )
        if created3:
            # Attach 2 demo defect photos
            photo1_content = generate_demo_defect_image("BORE OVERSIZE DEFECT", "Measured: 120.350mm (Max: 120.100mm)")
            dp1 = DefectPhoto.objects.create(
                inspection=insp3,
                caption="Optical bore gauge non-conformance reading (+0.250mm over max)"
            )
            dp1.image.save("bore_oversize_1.jpg", photo1_content, save=True)

            photo2_content = generate_demo_defect_image("INTERNAL SURFACE CHATTER", "Micro-grooves along bore axis")
            dp2 = DefectPhoto.objects.create(
                inspection=insp3,
                caption="Internal bore surface finish chatter markings"
            )
            dp2.image.save("bore_chatter_2.jpg", photo2_content, save=True)

            self.stdout.write(self.style.SUCCESS(f"  + Created Pending FAIL Inspection #{insp3.id} with 2 defect photos for {job3.job_number}"))

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Factory QC demo environment successfully seeded!"))
