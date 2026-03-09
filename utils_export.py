"""
📊 EXPORT UTILITIES MODULE
PDF/CSV report generation with filtering and formatting

Features:
- CSV export with configurable columns and filtering
- PDF report generation using reportlab
- Date range filtering for all exports
- Status filtering for interventions and SLA
- Responsive PDF layouts

Usage:
    from utils_export import generate_csv, generate_pdf_report
    
    # CSV Export
    csv_data = generate_csv(rows, headers, filename)
    
    # PDF Report
    pdf_bytes = generate_pdf_report(title, headers, data, filename)
"""

import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether, PageTemplate, Frame
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from flask import current_app
from io import BytesIO


# ============================================================
# CSV EXPORT FUNCTIONS
# ============================================================

def generate_csv(
    rows: List[Dict[str, Any]],
    headers: List[str],
    filename: str = None
) -> Tuple[bytes, str]:
    """
    Generate CSV export from list of dicts.
    
    Args:
        rows: List of dictionaries containing row data
        headers: List of header names (keys to extract from each row)
        filename: Optional filename for Content-Disposition header
    
    Returns:
        Tuple of (csv_bytes, filename)
    
    Example:
        csv_data, fname = generate_csv(
            [{'id': 1, 'name': 'John', 'status': 'active'}],
            headers=['id', 'name', 'status'],
            filename='export.csv'
        )
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    
    # Write header
    writer.writeheader()
    
    # Write rows - only include specified headers
    for row in rows:
        filtered_row = {h: row.get(h, '') for h in headers}
        writer.writerow(filtered_row)
    
    csv_bytes = output.getvalue().encode('utf-8-sig')  # UTF-8 BOM for Excel compatibility
    
    if not filename:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return csv_bytes, filename


# ============================================================
# PDF REPORT GENERATION FUNCTIONS
# ============================================================

class PDFReport:
    """PDF Report generator with formatting utilities."""
    
    def __init__(self, title: str, filename: str = None, landscape_mode: bool = False):
        """
        Initialize PDF report.
        
        Args:
            title: Report title
            filename: Output filename
            landscape_mode: Use landscape orientation
        """
        self.title = title
        self.filename = filename or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.landscape = landscape_mode
        self.pagesize = landscape(A4) if landscape_mode else A4
        self.width, self.height = self.pagesize
        self.story = []
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#374151'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=6
        ))
    
    def add_title(self, title: str = None):
        """Add centered title."""
        title_text = title or self.title
        self.story.append(Paragraph(title_text, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.2 * inch))
    
    def add_heading(self, text: str):
        """Add section heading."""
        self.story.append(Paragraph(text, self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.1 * inch))
    
    def add_metadata(self, metadata: Dict[str, str]):
        """Add metadata section (date range, filters, etc)."""
        meta_text = ' | '.join([f"<b>{k}:</b> {v}" for k, v in metadata.items()])
        self.story.append(Paragraph(meta_text, self.styles['SmallText']))
        self.story.append(Spacer(1, 0.15 * inch))
    
    def add_table(
        self,
        data: List[List[str]],
        headers: List[str] = None,
        col_widths: List[float] = None,
        header_bg: str = '#1f2937',
        header_text: str = '#ffffff',
        row_bg: str = '#ffffff',
        alt_row_bg: str = '#f3f4f6'
    ):
        """
        Add formatted table to report.
        
        Args:
            data: List of rows (each row is list of cell values)
            headers: Optional list of header texts
            col_widths: Optional list of column widths in inches
            header_bg: Header background color (hex)
            header_text: Header text color (hex)
            row_bg: Normal row background (hex)
            alt_row_bg: Alternate row background (hex)
        """
        # Prepare table data
        table_data = []
        if headers:
            table_data.append(headers)
        table_data.extend(data)
        
        # Calculate column widths
        if not col_widths:
            # Auto-distribute available width
            num_cols = len(table_data[0]) if table_data else 1
            available_width = self.width - (0.5 * inch)
            col_widths = [available_width / num_cols] * num_cols
        
        # Create table
        table = Table(table_data, colWidths=col_widths)
        
        # Apply styling
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(header_text)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor(row_bg), colors.HexColor(alt_row_bg)]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]
        
        table.setStyle(TableStyle(style_commands))
        self.story.append(table)
        self.story.append(Spacer(1, 0.2 * inch))
    
    def add_paragraph(self, text: str, style: str = 'Normal'):
        """Add paragraph text."""
        self.story.append(Paragraph(text, self.styles[style]))
        self.story.append(Spacer(1, 0.1 * inch))
    
    def add_spacer(self, height: float = 0.2):
        """Add vertical spacer (in inches)."""
        self.story.append(Spacer(1, height * inch))
    
    def add_page_break(self):
        """Add page break."""
        self.story.append(PageBreak())
    
    def build(self) -> bytes:
        """Build PDF and return bytes."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            title=self.title
        )
        
        doc.build(self.story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


# ============================================================
# DATA FORMATTING HELPERS
# ============================================================

def format_datetime(dt: datetime, format_str: str = '%d/%m/%Y %H:%M') -> str:
    """Format datetime object to string."""
    if not dt:
        return '-'
    if isinstance(dt, str):
        return dt
    return dt.strftime(format_str)


def format_currency(value: float, currency: str = 'DZD') -> str:
    """Format currency value."""
    if value is None:
        return '-'
    return f"{value:,.2f} {currency}"


def format_status(status: str) -> str:
    """Format status with French translation."""
    status_map = {
        'en_cours': 'En cours',
        'valide': 'Validée',
        'termine': 'Terminée',
        'annulee': 'Annulée',
        'pending': 'En attente',
        'approved': 'Approuvée',
        'rejected': 'Rejetée',
        'entree': 'Entrée',
        'sortie': 'Sortie',
        'adjustment': 'Ajustement'
    }
    return status_map.get(status, status)


def apply_date_filter(
    items: List[Any],
    date_field: str,
    date_debut: str = None,
    date_fin: str = None
) -> List[Any]:
    """
    Filter items by date range.
    
    Args:
        items: List of items to filter
        date_field: Name of date attribute/field
        date_debut: Start date (YYYY-MM-DD)
        date_fin: End date (YYYY-MM-DD)
    
    Returns:
        Filtered list
    """
    if not date_debut and not date_fin:
        return items
    
    filtered = []
    
    if date_debut:
        try:
            start_date = datetime.strptime(date_debut, '%Y-%m-%d').date()
        except:
            start_date = None
    else:
        start_date = None
    
    if date_fin:
        try:
            end_date = datetime.strptime(date_fin, '%Y-%m-%d').date()
        except:
            end_date = None
    else:
        end_date = None
    
    for item in items:
        dt = getattr(item, date_field, None)
        if not dt:
            continue
        
        # Handle both datetime and date objects
        if hasattr(dt, 'date'):
            item_date = dt.date()
        else:
            item_date = dt
        
        if start_date and item_date < start_date:
            continue
        if end_date and item_date > end_date:
            continue
        
        filtered.append(item)
    
    return filtered


def apply_status_filter(
    items: List[Any],
    status_field: str,
    status: str = None
) -> List[Any]:
    """
    Filter items by status.
    
    Args:
        items: List of items to filter
        status_field: Name of status attribute/field
        status: Status value to filter by
    
    Returns:
        Filtered list
    """
    if not status:
        return items
    
    return [item for item in items if getattr(item, status_field, None) == status]


# ============================================================
# EXPORT STATISTICS
# ============================================================

def calculate_export_stats(items: List[Any], stat_fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculate statistics from items.
    
    Args:
        items: List of items
        stat_fields: Dict of {stat_name: field_name} for numeric summation
    
    Returns:
        Dict of calculated statistics
    """
    stats = {
        'total_items': len(items),
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    for stat_name, field_name in stat_fields.items():
        try:
            total = sum(float(getattr(item, field_name, 0) or 0) for item in items)
            stats[stat_name] = f"{total:,.2f}"
        except:
            stats[stat_name] = 'N/A'
    
    return stats
