from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
from config.settings import settings
from datetime import datetime


class PDFGenerator:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.reports_dir

    def _output_path(self, name: str) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return self.base_dir / f"{name}_{timestamp}.pdf"

    def simple_doc(self, title: str, lines: list[str]) -> Path:
        path = self._output_path(title.replace(' ', '_').lower())
        c = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont('Helvetica-Bold', 16)
        c.drawString(50, y, title)
        y -= 30
        c.setFont('Helvetica', 10)
        for line in lines:
            c.drawString(50, y, line)
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont('Helvetica', 10)
        c.showPage()
        c.save()
        return path

    def build_table_doc(self, title: str, headers: list[str], rows: list[list[str]]) -> Path:
        path = self._output_path(title.replace(' ', '_').lower())
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = [Paragraph(title, styles['Title']), Spacer(1, 12)]
        data = [headers] + rows
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightyellow]),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ]))
        story.append(table)
        doc.build(story)
        return path

__all__ = ['PDFGenerator']
