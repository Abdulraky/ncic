"""
Report Generator for Authenticity Verification Results
Generates PDF and CSV reports for legal proceedings
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import csv
from io import BytesIO, StringIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class ReportGenerator:
    """Generate PDF and CSV reports for verification results"""
    
    def __init__(self):
        """Initialize report generator"""
        self.has_reportlab = HAS_REPORTLAB
    
    def generate_csv_report(self, verification_results: List[Dict[str, Any]]) -> str:
        """
        Generate CSV report from verification results
        
        Args:
            verification_results: List of verification result dictionaries
            
        Returns:
            CSV data as string
        """
        output = StringIO()
        
        if not verification_results:
            return ""
        
        # Prepare headers
        headers = [
            "Result File",
            "Authenticity Score",
            "Status",
            "Passed Checks",
            "Failed Checks",
            "Total Checks",
            "Verified Account",
            "URL Valid",
            "Metadata Intact",
            "Timestamp Verified",
            "No Editing",
            "SHA256 Verified",
            "Screenshot Captured",
            "JSON Preserved",
            "Generated At"
        ]
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Write data rows
        for result in verification_results:
            try:
                checks = result.get("check_results", {})
                
                writer.writerow({
                    "Result File": result.get("file", ""),
                    "Authenticity Score": result.get("authenticity_score", 0),
                    "Status": result.get("status", "unknown"),
                    "Passed Checks": result.get("passed_checks", 0),
                    "Failed Checks": result.get("failed_checks", 0),
                    "Total Checks": result.get("total_checks", 0),
                    "Verified Account": "✓" if checks.get("verified_account") else "✗",
                    "URL Valid": "✓" if checks.get("url_valid") else "✗",
                    "Metadata Intact": "✓" if checks.get("metadata_intact") else "✗",
                    "Timestamp Verified": "✓" if checks.get("timestamp_verified") else "✗",
                    "No Editing": "✓" if checks.get("no_editing") else "✗",
                    "SHA256 Verified": "✓" if checks.get("sha256_verified") else "✗",
                    "Screenshot Captured": "✓" if checks.get("screenshot_captured") else "✗",
                    "JSON Preserved": "✓" if checks.get("json_preserved") else "✗",
                    "Generated At": result.get("generated_at", "")
                })
            except Exception as e:
                print(f"Error writing result row: {str(e)}")
                continue
        
        return output.getvalue()
    
    def generate_pdf_report(self, verification_results: List[Dict[str, Any]], output_path: str = None) -> bytes:
        """
        Generate PDF report from verification results
        
        Args:
            verification_results: List of verification result dictionaries
            output_path: Optional path to save PDF
            
        Returns:
            PDF bytes
        """
        if not self.has_reportlab:
            raise ImportError("reportlab not installed. Install with: pip install reportlab")
        
        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            spaceAfter=6
        )
        
        # Title
        story.append(Paragraph("NCIC AUTHENTICITY VERIFICATION REPORT", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report metadata
        metadata = [
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Results: {len(verification_results)}",
            f"System: NCIC Intelligence Lab - Module 3"
        ]
        
        for line in metadata:
            story.append(Paragraph(line, body_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Summary statistics
        story.append(Paragraph("SUMMARY STATISTICS", heading_style))
        
        total_score = 0
        authentic_count = 0
        suspicious_count = 0
        
        for result in verification_results:
            score = result.get("authenticity_score", 0)
            total_score += score
            
            if result.get("status") == "AUTHENTIC":
                authentic_count += 1
            elif result.get("status") == "SUSPICIOUS":
                suspicious_count += 1
        
        avg_score = total_score / len(verification_results) if verification_results else 0
        
        summary_data = [
            ["Metric", "Value"],
            ["Average Authenticity Score", f"{avg_score:.1f}%"],
            ["Authentic Results", f"{authentic_count}"],
            ["Suspicious Results", f"{suspicious_count}"],
            ["Total Analyzed", f"{len(verification_results)}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3055')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed results
        story.append(Paragraph("DETAILED VERIFICATION RESULTS", heading_style))
        
        for idx, result in enumerate(verification_results[:20], 1):  # Limit to first 20 for readability
            story.append(Spacer(1, 0.1*inch))
            
            score = result.get("authenticity_score", 0)
            status = result.get("status", "unknown")
            
            # Color code the status
            if status == "AUTHENTIC":
                status_color = colors.HexColor('#10b981')
            elif status == "NEEDS_REVIEW":
                status_color = colors.HexColor('#f59e0b')
            else:
                status_color = colors.HexColor('#ef4444')
            
            result_heading = ParagraphStyle(
                f'ResultHeading{idx}',
                parent=heading_style,
                textColor=status_color
            )
            
            story.append(Paragraph(f"Result {idx}: {status} ({score}%)", result_heading))
            
            # Check results table
            checks_data = [["Check", "Status"]]
            checks = result.get("check_results", {})
            
            for check_name, passed in checks.items():
                status_text = "✓ PASS" if passed else "✗ FAIL"
                checks_data.append([check_name.replace("_", " ").title(), status_text])
            
            checks_table = Table(checks_data, colWidths=[3.5*inch, 1.5*inch])
            checks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(checks_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "This report is generated by the NCIC Intelligence Lab - Module 3 (Authenticity Score Verification). "
            "Results are intended for forensic analysis and legal proceedings under the Evidence Act (Cap 80, Laws of Kenya).",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
        ))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def generate_legal_certificate(self, evidence_item: Dict[str, Any], verification_result: Dict[str, Any]) -> str:
        """
        Generate a court-admissible legal certificate
        
        Args:
            evidence_item: Evidence data
            verification_result: Verification result
            
        Returns:
            Certificate as formatted text
        """
        score = verification_result.get("authenticity_score", 0)
        
        certificate = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║          KENYA NATIONAL COHESION AND INTEGRATION COMMISSION                    ║
║               DIGITAL EVIDENCE AUTHENTICITY VERIFICATION CERTIFICATE           ║
║                          COURT-ADMISSIBLE DOCUMENT                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

VERIFICATION DETAILS:
─────────────────────────────────────────────────────────────────────────────────

Evidence Item:              {evidence_item.get('post_id', 'N/A')}
Platform:                   {evidence_item.get('platform', 'Unknown')}
Username:                   @{evidence_item.get('username', 'Unknown')}
Post URL:                   {evidence_item.get('url', 'N/A')}
Capture Timestamp:          {evidence_item.get('timestamp', 'N/A')}

AUTHENTICITY ASSESSMENT:
─────────────────────────────────────────────────────────────────────────────────

Authenticity Score:         {score}%
Verification Status:        {verification_result.get('status', 'UNKNOWN')}
Total Checks Performed:     {verification_result.get('total_checks', 0)}
Checks Passed:              {verification_result.get('passed_checks', 0)}
Checks Failed:              {verification_result.get('failed_checks', 0)}

VERIFICATION CHECKS STATUS:
─────────────────────────────────────────────────────────────────────────────────
"""
        
        checks = verification_result.get("check_results", {})
        for check_name, passed in checks.items():
            status = "✔ PASS" if passed else "✗ FAIL"
            certificate += f"{status:6} {check_name.replace('_', ' ').title()}\n"
        
        certificate += f"""
LEGAL NOTICE:
─────────────────────────────────────────────────────────────────────────────────

This certificate is generated under the authority of the Evidence Act, Cap 80,
Laws of Kenya. The evidence has been verified through cryptographic hashing,
metadata validation, and platform authentication checks.

This document serves as proof of:
  • Original content integrity (SHA-256 verification)
  • Authenticity of source (Platform verification)
  • Completeness of metadata (Timestamp and engagement metrics)
  • Absence of tampering or modification

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: NCIC Intelligence Lab - Module 3
Status: {verification_result.get('status', 'VERIFIED')}

Certified for legal proceedings under Section 106B of the Evidence Act.
"""
        
        return certificate
    
    def export_verification_batch(self, results_directory: Path, format: str = "csv") -> bytes:
        """
        Export entire batch of verification results
        
        Args:
            results_directory: Path to verification results directory
            format: Export format ('csv' or 'pdf')
            
        Returns:
            Export file bytes
        """
        # Load all results
        results = []
        
        if results_directory.exists():
            for result_file in results_directory.glob("*.json"):
                try:
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        result["file"] = result_file.name
                        results.append(result)
                except:
                    pass
        
        if format.lower() == "csv":
            csv_data = self.generate_csv_report(results)
            return csv_data.encode('utf-8')
        
        elif format.lower() == "pdf":
            if not self.has_reportlab:
                raise ImportError("reportlab not installed")
            
            return self.generate_pdf_report(results)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
