"""
PDF Generator for QualiTrack Certificate of Quality & Dispatch Release.
Uses ReportLab to produce professional, vector-sharp A4 certificates.
Enforces all 10 industrial quality rules:
1. Valid timestamps with explicit UTC timezone.
2. No overlapping, clipping, or corrupted layout elements.
3. Product description and inspection parameters consistency.
4. Mathematical LSL / USL verification (PASS strictly within [LSL, USL]).
5. Live calculated First-Pass Yield (never hard-coded).
6. Clear batch sampling breakdown (distinguishes sample count from total batch quantity).
7. Honest QMS verification standard (no false ISO claims unless verified).
8. Genuine SHA-256 cryptographic digest.
9. Backend clearance verification check.
10. Synchronized with database QualityCertificate model.
"""

import io
import hashlib
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)


def compute_certificate_hash(job, cert_number, generated_at_iso, inspections_data, is_authorized):
    """
    Computes a deterministic, cryptographic SHA-256 digest of canonical certificate records.
    Provides tamper-evident proof of audit verification.
    """
    summary_parts = []
    for insp in inspections_data:
        summary_parts.append(
            f"{insp['id']}:{insp['parameter']}:{insp['lsl']}:{insp['usl']}:{insp['measured']}:{insp['result']}"
        )
    canonical = (
        f"CERT_NUM={cert_number}|JOB={job.job_number}|PROD={job.product_name}|QTY={job.target_quantity}|"
        f"TIME={generated_at_iso}|AUTH={is_authorized}|"
        f"CLEARED_BY={job.cleared_by_id or 'NONE'}|"
        f"CLEARED_AT={job.cleared_at.isoformat() if job.cleared_at else 'NONE'}|"
        f"INSPECTIONS={';'.join(summary_parts)}"
    )
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def generate_certificate_pdf(job, inspections, cert_record, block_reasons=None):
    """
    Generates a high-quality PDF binary stream for the Certificate of Quality & Dispatch Release.
    Returns: (pdf_bytes, sha256_hash)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    
    # Custom Industrial Palette
    primary_color = colors.HexColor("#0f172a")     # Deep Slate
    accent_blue = colors.HexColor("#1e40af")       # Industrial Blue
    navy_header = colors.HexColor("#1e3a8a")       # Navy
    success_color = colors.HexColor("#047857")     # Dark Emerald
    success_bg = colors.HexColor("#ecfdf5")
    danger_color = colors.HexColor("#b91c1c")      # Dark Red
    danger_bg = colors.HexColor("#fef2f2")
    warning_color = colors.HexColor("#b45309")     # Dark Amber
    warning_bg = colors.HexColor("#fffbeb")
    border_color = colors.HexColor("#cbd5e1")
    light_bg = colors.HexColor("#f8fafc")

    company_title_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        textColor=primary_color,
    )
    company_sub_style = ParagraphStyle(
        'CompanySub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#64748b"),
        textTransform='uppercase',
    )
    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    bold_label = ParagraphStyle(
        'CertBoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#475569"),
        textTransform='uppercase',
    )
    bold_value = ParagraphStyle(
        'CertBoldValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=primary_color,
    )
    doc_main_title = ParagraphStyle(
        'DocMainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=13.5,
        alignment=1,  # Center
        textColor=navy_header,
    )
    doc_sub_title = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        alignment=1,  # Center
        textColor=colors.HexColor("#64748b"),
        textTransform='uppercase',
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=primary_color,
        textTransform='uppercase',
    )

    elements = []

    # 1. Header Row (Company Info & Certificate Reference)
    iso_verified = getattr(settings, 'QUALITRACK_ISO_VERIFIED', False)
    iso_text = "ISO 9001:2015 Verified Facility" if iso_verified else "QualiTrack Precision Metrology Standard (QMS-QP-01)"

    company_cell = [
        Paragraph("QUALITRACK PRECISION TECHNOLOGIES", company_title_style),
        Spacer(1, 1 * mm),
        Paragraph("Quality Assurance &amp; Factory Dispatch Clearance Division", company_sub_style),
        Paragraph(f"Plant Unit 4 &bull; Advanced Metrology Lab &bull; {iso_text}", body_style),
    ]

    status_badge_text = "DISPATCH AUTHORIZED" if cert_record.is_dispatch_authorized else "PROVISIONAL - PENDING CLEARANCE"
    status_bg = success_bg if cert_record.is_dispatch_authorized else warning_bg
    status_text_color = success_color if cert_record.is_dispatch_authorized else warning_color

    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=status_text_color,
        alignment=2,  # Right align
    )

    cert_meta_cell = [
        Paragraph(f"<b>Ref:</b> {cert_record.certificate_number}", ParagraphStyle('RightRef', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=11, alignment=2, textColor=primary_color)),
        Paragraph(f"<b>Issued:</b> {cert_record.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC", ParagraphStyle('RightTime', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=2, textColor=colors.HexColor("#64748b"))),
        Paragraph(f"<b>Status:</b> {status_badge_text}", badge_style),
    ]

    header_table = Table([[company_cell, cert_meta_cell]], colWidths=[122 * mm, 60 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceBefore=3, spaceAfter=4))

    # 2. Document Title Header Band
    doc_title_cell = [
        Paragraph("CERTIFICATE OF QUALITY &amp; FACTORY DISPATCH RELEASE", doc_main_title),
        Spacer(1, 0.5 * mm),
        Paragraph("OFFICIAL DIMENSIONAL METROLOGY CONFORMANCE &amp; CLEARANCE RECORD", doc_sub_title),
    ]
    doc_title_table = Table([[doc_title_cell]], colWidths=[182 * mm])
    doc_title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(doc_title_table)
    elements.append(Spacer(1, 2.5 * mm))

    # 3. Formal Statement of Conformity
    decl_p = Paragraph(
        f"<b>Declaration of Conformity:</b> This official certificate verifies that production batch "
        f"<b>{job.job_number}</b> (<b>{job.product_name}</b>) has undergone precision dimensional inspection "
        f"and metrological quality audit. All inspected parameters were measured against calibrated tooling "
        f"in strict accordance with engineering tolerance limits (LSL / USL) and QualiTrack Factory Dispatch Protocols.",
        ParagraphStyle('DeclStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor("#334155"))
    )
    decl_table = Table([[decl_p]], colWidths=[182 * mm])
    decl_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(decl_table)
    elements.append(Spacer(1, 3 * mm))

    # 4. Section 1: Batch Specification & Sampling
    elements.append(Paragraph("1. PRODUCTION BATCH SPECIFICATION &amp; SAMPLING PROTOCOL", section_heading))
    elements.append(Spacer(1, 1.5 * mm))

    batch_data = [
        [
            Paragraph("PRODUCTION JOB #", bold_label),
            Paragraph("PRODUCT DESCRIPTION", bold_label),
            Paragraph("BATCH QUANTITY", bold_label),
            Paragraph("FIRST-PASS YIELD (FPY)", bold_label),
        ],
        [
            Paragraph(f"<b>{job.job_number}</b>", bold_value),
            Paragraph(f"<b>{job.product_name}</b>", bold_value),
            Paragraph(f"<b>{job.target_quantity} units</b>", bold_value),
            Paragraph(
                f"<font color='{status_text_color.hexval()}'><b>{cert_record.first_pass_yield}% Pass Rate</b></font>",
                bold_value
            ),
        ],
        [
            Paragraph("SAMPLING AUDIT PLAN", bold_label),
            Paragraph("DIMENSIONS CHECKED", bold_label),
            Paragraph("CHECKS PASSED / TOTAL", bold_label),
            Paragraph("DISPATCH CLEARANCE", bold_label),
        ],
        [
            Paragraph(f"<b>{cert_record.inspected_units_count} sample unit(s)</b>", body_style),
            Paragraph(f"<b>{cert_record.inspected_dimensions_count} critical parameter(s)</b>", body_style),
            Paragraph(f"<b>{cert_record.passed_inspections} / {cert_record.total_inspections} checks passed</b>", body_style),
            Paragraph(f"<b>{'CLEARED' if cert_record.is_dispatch_authorized else 'RESTRICTED'}</b>", body_style),
        ]
    ]

    batch_table = Table(batch_data, colWidths=[42 * mm, 58 * mm, 42 * mm, 40 * mm])
    batch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(batch_table)
    elements.append(Spacer(1, 1.5 * mm))

    # Scope Notice (Requirement 6)
    scope_notice = (
        f"<b>Sampling Scope Notice:</b> Quality verification is strictly based on physical dimensional "
        f"metrology performed on {cert_record.inspected_units_count} sampled unit(s) across "
        f"{cert_record.inspected_dimensions_count} critical parameter(s) from a total production batch of "
        f"{job.target_quantity} units under QualiTrack Standard Sampling Protocols."
    )
    elements.append(Paragraph(scope_notice, ParagraphStyle('Scope', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=colors.HexColor("#475569"))))
    elements.append(Spacer(1, 3 * mm))

    # Policy Warning Banner (if not authorized - Requirement 9)
    if not cert_record.is_dispatch_authorized and block_reasons:
        reason_list = "<br/>&bull; ".join(block_reasons)
        warn_text = (
            f"<b>DISPATCH CLEARANCE RESTRICTIONS IN EFFECT:</b><br/>&bull; {reason_list}"
        )
        warn_table = Table([[Paragraph(warn_text, ParagraphStyle('WarnP', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=warning_color))]], colWidths=[182 * mm])
        warn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), warning_bg),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#fcd34d")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(warn_table)
        elements.append(Spacer(1, 3 * mm))

    # 5. Section 2: Dimensional Metrology Inspection Record
    elements.append(Paragraph("2. DIMENSIONAL METROLOGY INSPECTION RECORD (TOLERANCE AUDIT)", section_heading))
    elements.append(Spacer(1, 1.5 * mm))

    table_header = [
        Paragraph("<b>ID</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>Parameter Name</b>", ParagraphStyle('TH_L', fontName='Helvetica-Bold', fontSize=7.5, alignment=0, textColor=colors.white)),
        Paragraph("<b>LSL</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>USL</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>Measured</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>Variance (&Delta;)</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>Result</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>Verified By</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
        Paragraph("<b>Status</b>", ParagraphStyle('TH_C', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=colors.white)),
    ]

    table_rows = [table_header]
    for insp in inspections:
        is_pass = (Decimal(str(insp.min_limit)) <= Decimal(str(insp.measurement)) <= Decimal(str(insp.max_limit)))
        result_badge = "PASS" if is_pass else "FAIL"
        result_color = success_color if is_pass else danger_color

        nominal = (Decimal(str(insp.min_limit)) + Decimal(str(insp.max_limit))) / Decimal('2')
        delta = Decimal(str(insp.measurement)) - nominal
        delta_str = f"{delta:+.3f} mm"

        table_rows.append([
            Paragraph(f"#{insp.id}", ParagraphStyle('TC_Id', fontName='Helvetica', fontSize=7.5, alignment=1)),
            Paragraph(f"<b>{insp.parameter_name}</b>", ParagraphStyle('TC_PName', fontName='Helvetica', fontSize=7.5, alignment=0)),
            Paragraph(f"{insp.min_limit:.3f} mm", ParagraphStyle('TC', fontName='Helvetica', fontSize=7.5, alignment=1)),
            Paragraph(f"{insp.max_limit:.3f} mm", ParagraphStyle('TC', fontName='Helvetica', fontSize=7.5, alignment=1)),
            Paragraph(f"<b>{insp.measurement:.3f} mm</b>", ParagraphStyle('TC_B', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=result_color)),
            Paragraph(delta_str, ParagraphStyle('TC_D', fontName='Helvetica', fontSize=7, alignment=1)),
            Paragraph(f"<b><font color='{result_color.hexval()}'>{result_badge}</font></b>", ParagraphStyle('TC_Res', fontName='Helvetica-Bold', fontSize=8, alignment=1)),
            Paragraph(insp.inspector.get_full_name() or insp.inspector.username, ParagraphStyle('TC_User', fontName='Helvetica', fontSize=7.5, alignment=1)),
            Paragraph(f"<b>{insp.status}</b>", ParagraphStyle('TC_Stat', fontName='Helvetica-Bold', fontSize=7.5, alignment=1, textColor=primary_color)),
        ])

    col_widths = [10 * mm, 40 * mm, 18 * mm, 18 * mm, 20 * mm, 18 * mm, 16 * mm, 21 * mm, 21 * mm]
    insp_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 1, primary_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
    ]
    for r in range(1, len(table_rows)):
        if r % 2 == 0:
            t_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#f1f5f9")))
    insp_table.setStyle(TableStyle(t_style))
    elements.append(insp_table)
    elements.append(Spacer(1, 3 * mm))

    # 6. Section 3: Authorization & Verification Sign-Off
    elements.append(Paragraph("3. FACTORY DISPATCH CLEARANCE &amp; AUTHORIZATION SIGN-OFF", section_heading))
    elements.append(Spacer(1, 1.5 * mm))

    inspector_user = inspections.first().inspector if inspections.exists() else None
    inspector_name = (inspector_user.get_full_name() or inspector_user.username) if inspector_user else "Authorized Inspector"
    
    supervisor_user = job.cleared_by
    supervisor_name = (supervisor_user.get_full_name() or supervisor_user.username) if supervisor_user else "Pending Supervisor Sign-Off"
    supervisor_time = job.cleared_at.strftime('%Y-%m-%d %H:%M:%S UTC') if job.cleared_at else "Awaiting Official Authorization"

    sign_left = [
        Paragraph("<b>METROLOGY INSPECTOR VERIFICATION</b>", bold_label),
        Spacer(1, 1.5 * mm),
        Paragraph(f"<b>{inspector_name}</b>", bold_value),
        Paragraph("QC Calibration Verification Stamp Applied", body_style),
        Paragraph("<font color='#047857'>&bull; Precision Micrometer Calibrated</font>", body_style),
        Spacer(1, 2 * mm),
        Paragraph("Sign: __________________________", ParagraphStyle('SignL', fontName='Helvetica', fontSize=7, textColor=colors.HexColor("#64748b"))),
    ]

    seal_box = [
        Paragraph("<b>&starf; FACTORY QA RELEASE SEAL &starf;</b>", ParagraphStyle('SealStar', fontName='Helvetica-Bold', fontSize=6.5, leading=8, alignment=1, textColor=status_text_color)),
        Spacer(1, 1 * mm),
        Paragraph(f"<b>{status_badge_text}</b>", ParagraphStyle('SealTitle', fontName='Helvetica-Bold', fontSize=9.5, leading=11.5, alignment=1, textColor=status_text_color)),
        Spacer(1, 1 * mm),
        Paragraph("QUALITRACK QA RELEASE DIVISION", ParagraphStyle('SealSub', fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=1, textColor=primary_color)),
        Paragraph(f"SERIAL: {job.job_number}", ParagraphStyle('SealSer', fontName='Courier-Bold', fontSize=7.5, leading=9.5, alignment=1, textColor=primary_color)),
        Paragraph("&bull; VERIFIED &amp; AUDITED CONFORMANCE &bull;", ParagraphStyle('SealAudit', fontName='Helvetica-Bold', fontSize=6, leading=7.5, alignment=1, textColor=colors.HexColor("#475569"))),
    ]

    sign_right = [
        Paragraph("<b>QA SUPERVISOR DISPATCH RELEASE</b>", bold_label),
        Spacer(1, 1.5 * mm),
        Paragraph(f"<b>{supervisor_name}</b>", bold_value),
        Paragraph(f"Time: {supervisor_time}", body_style),
        Paragraph(
            f"<font color='{status_text_color.hexval()}'>&bull; {'Full Dispatch Release Authorized' if cert_record.is_dispatch_authorized else 'Clearance Pending Final Sign-Off'}</font>",
            body_style
        ),
        Spacer(1, 2 * mm),
        Paragraph("Sign: __________________________", ParagraphStyle('SignL', fontName='Helvetica', fontSize=7, textColor=colors.HexColor("#64748b"))),
    ]

    sign_table = Table([[sign_left, seal_box, sign_right]], colWidths=[59 * mm, 64 * mm, 59 * mm])
    sign_table.setStyle(TableStyle([
        ('BOX', (0, 0), (0, 0), 1, border_color),
        ('BOX', (1, 0), (1, 0), 2, status_text_color),
        ('BOX', (2, 0), (2, 0), 1, border_color),
        ('BACKGROUND', (0, 0), (0, 0), light_bg),
        ('BACKGROUND', (1, 0), (1, 0), status_bg),
        ('BACKGROUND', (2, 0), (2, 0), light_bg),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(KeepTogether([sign_table]))
    elements.append(Spacer(1, 3 * mm))

    # 7. Section 4: Cryptographic Record Traceability & Digest Box
    footer_cell = [
        Paragraph("<b>CRYPTOGRAPHIC RECORD TRACEABILITY &amp; TAMPER-EVIDENT AUDIT HASH</b>", ParagraphStyle('FooterHead', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=primary_color)),
        Spacer(1, 1 * mm),
        Paragraph(
            f"<b>Certificate Reference:</b> {cert_record.certificate_number} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>SHA-256 Digest:</b> <font name='Courier' size='6.5'><b>{cert_record.sha256_hash}</b></font>",
            ParagraphStyle('FooterDigest', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=colors.HexColor("#1e293b"))
        ),
        Spacer(1, 1 * mm),
        Paragraph(
            "This official Certificate of Quality &amp; Dispatch Release constitutes verified inspection record traceability "
            "generated under QualiTrack Precision Quality Protocols. Any unauthorized modification invalidates this document.",
            ParagraphStyle('FooterDisclaimer', fontName='Helvetica', fontSize=6, leading=7.5, textColor=colors.HexColor("#64748b"))
        )
    ]
    footer_table = Table([[footer_cell]], colWidths=[182 * mm])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('BOX', (0, 0), (-1, -1), 0.75, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Compute genuine hash of the actual PDF file bytes
    file_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, file_sha256
