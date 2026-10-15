from __future__ import annotations

from pathlib import Path

from config import OUTPUT_MD_PATH
from utils.helpers import ensure_directory


class MarkdownService:
    def write_report(self, content: str, output_path: str | Path | None = None) -> Path:
        path = Path(output_path or OUTPUT_MD_PATH)
        ensure_directory(path.parent)
        path.write_text(content, encoding="utf-8")
        return path
