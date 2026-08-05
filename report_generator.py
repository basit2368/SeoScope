import os
import csv
import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String


def generate_pdf_report(audit_data, output_path=None):
    """
    Generates a professional multi-page PDF audit report using ReportLab.
    Returns file bytes if output_path is None, or writes to output_path.
    """
    buffer = io.BytesIO() if output_path is None else output_path

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a')
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    elements = []

    # --- Header Banner ---
    elements.append(Paragraph("SEOScope Audit Report", title_style))
    elements.append(Paragraph(f"Automated Website Analysis & SEO Diagnostic &bull; Generated: {audit_data.get('audit_date', '')}", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=12))

    # --- Summary Box ---
    scores = audit_data.get('scores', {})
    overall_score = scores.get('overall_score', 0)
    rating_grade = scores.get('rating_grade', 'N/A')
    rating_color_hex = scores.get('rating_color', '#3b82f6')
    rating_color = colors.HexColor(rating_color_hex)

    summary_data = [
        [
            Paragraph("<b>Target URL:</b>", body_style),
            Paragraph(f"<font color='#0284c7'><u>{audit_data.get('target_url', '')}</u></font>", body_style)
        ],
        [
            Paragraph("<b>Overall SEO Score:</b>", body_style),
            Paragraph(f"<font size='14' color='{rating_color_hex}'><b>{overall_score} / 100</b> ({rating_grade})</font>", body_style)
        ],
        [
            Paragraph("<b>Response Time:</b>", body_style),
            Paragraph(f"{audit_data.get('response_time_ms', 0)} ms", body_style)
        ],
        [
            Paragraph("<b>Total Issues Found:</b>", body_style),
            Paragraph(f"<b>{scores.get('summary', {}).get('critical_count', 0)}</b> Critical, <b>{scores.get('summary', {}).get('warning_count', 0)}</b> Warnings, <b>{scores.get('summary', {}).get('passed_count', 0)}</b> Passed", body_style)
        ]
    ]

    summary_table = Table(summary_data, colWidths=[130, 410])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # --- Category Breakdown Table ---
    elements.append(Paragraph("Category Performance Scores", section_heading))
    
    cat_scores = scores.get('category_scores', {})
    cat_table_data = [
        [Paragraph("<b>Category</b>", body_style), Paragraph("<b>Score %</b>", body_style), Paragraph("<b>Status</b>", body_style)],
        [Paragraph("Technical SEO", body_style), f"{cat_scores.get('technical', 0)}%", "Pass" if cat_scores.get('technical', 0) >= 70 else "Needs Work"],
        [Paragraph("Content Optimization", body_style), f"{cat_scores.get('content', 0)}%", "Pass" if cat_scores.get('content', 0) >= 70 else "Needs Work"],
        [Paragraph("Image Optimization", body_style), f"{cat_scores.get('images', 0)}%", "Pass" if cat_scores.get('images', 0) >= 70 else "Needs Work"],
        [Paragraph("Links & Architecture", body_style), f"{cat_scores.get('links', 0)}%", "Pass" if cat_scores.get('links', 0) >= 70 else "Needs Work"]
    ]

    cat_table = Table(cat_table_data, colWidths=[240, 150, 150])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 14))

    # --- Critical Issues Section ---
    criticals = scores.get('issues', {}).get('critical', [])
    if criticals:
        elements.append(Paragraph("<font color='#dc2626'>Critical SEO Issues (High Priority)</font>", section_heading))
        crit_rows = [[Paragraph("<b>Issue Title</b>", body_style), Paragraph("<b>Description & Impact</b>", body_style)]]
        for item in criticals:
            crit_rows.append([
                Paragraph(f"<b>{item.get('title', '')}</b><br/><font color='#64748b'>{item.get('category', '')}</font>", body_style),
                Paragraph(item.get('description', ''), body_style)
            ])
        crit_table = Table(crit_rows, colWidths=[180, 360])
        crit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fee2e2')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fca5a5')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(crit_table)
        elements.append(Spacer(1, 14))

    # --- Warnings Section ---
    warnings = scores.get('issues', {}).get('warning', [])
    if warnings:
        elements.append(Paragraph("<font color='#d97706'>SEO Warnings (Medium Priority)</font>", section_heading))
        warn_rows = [[Paragraph("<b>Issue Title</b>", body_style), Paragraph("<b>Description</b>", body_style)]]
        for item in warnings[:10]:  # Limit top 10 for PDF length
            warn_rows.append([
                Paragraph(f"<b>{item.get('title', '')}</b><br/><font color='#64748b'>{item.get('category', '')}</font>", body_style),
                Paragraph(item.get('description', ''), body_style)
            ])
        warn_table = Table(warn_rows, colWidths=[180, 360])
        warn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fef3c7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fcd34d')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(warn_table)
        elements.append(Spacer(1, 14))

    # --- Priority Recommendations ---
    recs = scores.get('recommendations', [])
    if recs:
        elements.append(Paragraph("Actionable Improvement Recommendations", section_heading))
        rec_rows = [[Paragraph("<b>Priority</b>", body_style), Paragraph("<b>Action Item</b>", body_style), Paragraph("<b>How to Fix</b>", body_style)]]
        for r in recs:
            p_color = '#dc2626' if r.get('priority') == 'High' else '#d97706' if r.get('priority') == 'Medium' else '#2563eb'
            rec_rows.append([
                Paragraph(f"<font color='{p_color}'><b>{r.get('priority', '')}</b></font>", body_style),
                Paragraph(f"<b>{r.get('action', '')}</b><br/><font color='#64748b'>{r.get('category', '')}</font>", body_style),
                Paragraph(r.get('how_to_fix', ''), body_style)
            ])
        rec_table = Table(rec_rows, colWidths=[70, 160, 310])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(rec_table)

    doc.build(elements)

    if output_path is None:
        buffer.seek(0)
        return buffer.getvalue()
    return output_path


def generate_csv_report(audit_data):
    """
    Generates a CSV formatted string containing all audit findings and metrics.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['SEOScope Audit Report Export'])
    writer.writerow(['Target URL', audit_data.get('target_url', '')])
    writer.writerow(['Audit Date', audit_data.get('audit_date', '')])
    writer.writerow(['Overall Score', audit_data.get('scores', {}).get('overall_score', '')])
    writer.writerow(['Rating Grade', audit_data.get('scores', {}).get('rating_grade', '')])
    writer.writerow([])

    # Category Scores
    writer.writerow(['Category', 'Score %'])
    cat_scores = audit_data.get('scores', {}).get('category_scores', {})
    for cat, val in cat_scores.items():
        writer.writerow([cat.capitalize(), f"{val}%"])
    writer.writerow([])

    # All Issues
    writer.writerow(['Type', 'Category', 'Issue Title', 'Description', 'Impact'])
    issues = audit_data.get('scores', {}).get('issues', {})
    for item in issues.get('critical', []):
        writer.writerow(['Critical', item.get('category'), item.get('title'), item.get('description'), item.get('impact')])
    for item in issues.get('warning', []):
        writer.writerow(['Warning', item.get('category'), item.get('title'), item.get('description'), item.get('impact')])
    for item in issues.get('passed', []):
        writer.writerow(['Passed', item.get('category'), item.get('title'), item.get('description'), 'None'])
    writer.writerow([])

    # Recommendations
    writer.writerow(['Priority', 'Category', 'Action Required', 'How to Fix'])
    for r in audit_data.get('scores', {}).get('recommendations', []):
        writer.writerow([r.get('priority'), r.get('category'), r.get('action'), r.get('how_to_fix')])

    return output.getvalue()
