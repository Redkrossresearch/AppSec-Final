from collections import Counter
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors


def create_pdf_report(scan, destination):
    """Generate a detailed PDF report with code snippets and fix information."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use Platypus for better layout
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                          rightMargin=30, leftMargin=30,
                          topMargin=30, bottomMargin=30)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=0
    )
    story.append(Paragraph("AppSec Orchestrator - Security Scan Report", title_style))
    
    # Summary
    counts = Counter(f.severity for f in scan.findings)
    resolved = sum(1 for f in scan.findings if f.status in {"fixed", "accepted"})
    fixed = sum(1 for f in scan.findings if f.status == "fixed")
    
    summary_text = f"""
    <b>Project:</b> {scan.project.name}<br/>
    <b>Scan #:</b> {scan.id}<br/>
    <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    <b>Files Scanned:</b> {scan.total_files}<br/>
    <b>Total Findings:</b> {len(scan.findings)}<br/>
    <b>Critical:</b> {counts['critical']} | <b>High:</b> {counts['high']} | <b>Medium:</b> {counts['medium']} | <b>Low:</b> {counts['low']}<br/>
    <b>Fixed:</b> {fixed} | <b>Resolved:</b> {resolved}
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Findings by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    sorted_findings = sorted(scan.findings, 
                            key=lambda f: (severity_order.get(f.severity, 99), f.cvss_score or 0), 
                            reverse=True)
    
    story.append(Paragraph("Detailed Findings", styles['Heading2']))
    story.append(Spacer(1, 6))
    
    for idx, finding in enumerate(sorted_findings, 1):
        # Finding header
        severity_color = {
            'critical': '#ff0000',
            'high': '#ff6600',
            'medium': '#ffcc00',
            'low': '#0066cc',
            'info': '#666666'
        }.get(finding.severity, '#999999')
        
        header = f"""
        <font color="{severity_color}"><b>[{finding.severity.upper()}]</b></font> 
        {finding.title}<br/>
        <font size="8"><b>File:</b> {finding.file_path} : {finding.line_number or 'N/A'}</font>
        """
        story.append(Paragraph(header, styles['Normal']))
        
        # Finding details
        details = f"""
        <b>Rule:</b> {finding.rule_id}<br/>
        <b>Category:</b> {finding.category}<br/>
        <b>CVSS Score:</b> {finding.cvss_score:.1f}<br/>
        <b>Description:</b> {finding.description}<br/>
        <b>Recommendation:</b> {finding.recommendation}
        """
        story.append(Paragraph(details, styles['Normal']))
        
        # Code snippet
        if finding.line_text:
            code_style = ParagraphStyle(
                'Code',
                parent=styles['Normal'],
                fontName='Courier',
                fontSize=8,
                backColor=colors.HexColor('#f5f5f5'),
                textColor=colors.HexColor('#333333'),
                leftIndent=12
            )
            code_text = f"<b>Vulnerable Code:</b><br/>{finding.line_text[:200]}"
            story.append(Paragraph(code_text, code_style))
        
        # Fix information
        if finding.fixes:
            latest_fix = finding.fixes[-1]
            fix_status = f'<font color="green"><b>{latest_fix.status.upper()}</b></font>'
            fix_info = f"""
            <b>Fix Status:</b> {fix_status}<br/>
            <b>Explanation:</b> {latest_fix.explanation}
            """
            story.append(Paragraph(fix_info, styles['Normal']))
        
        story.append(Spacer(1, 12))
        
        # Page break every 3 findings
        if idx % 3 == 0 and idx < len(sorted_findings):
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    return path


    doc.save()
    return path
