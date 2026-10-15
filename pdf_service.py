from __future__ import annotations

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from config import OUTPUT_PDF_PATH
from utils.helpers import ensure_directory
from utils.logger import AppLogger

logger = AppLogger("pdf_service").get_logger()


class PdfService:
    def generate_pdf(self, markdown_text: str, output_path: str | Path | None = None) -> Path:
        path = Path(output_path or OUTPUT_PDF_PATH)
        ensure_directory(path.parent)
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Travel Plan Report", styles["Title"]))
        story.append(Spacer(1, 12))
        for line in markdown_text.splitlines():
            if line.startswith("#"):
                story.append(Paragraph(line.lstrip("# "), styles["Heading2"]))
            elif line.startswith("- "):
                story.append(Paragraph(line[2:], styles["BodyText"]))
            else:
                story.append(Paragraph(line, styles["BodyText"]))
            story.append(Spacer(1, 6))
        try:
            doc.build(story)
            logger.info("PDF generated successfully at %s", path)
            return path
        except Exception as exc:  # pragma: no cover
            logger.exception("PDF generation failed: %s", exc)
            raise RuntimeError("PDF generation failed") from exc
