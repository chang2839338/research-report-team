"""Local DOCX writing helpers.

The workflow never asks Codex or the OpenAI API to create Word files. The server
publishes DOCX locally from the final Markdown artifact.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile


def markdown_to_plain_text(markdown: str) -> str:
    text = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "- ", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("__", "")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def write_docx_from_markdown(markdown_path: Path, docx_path: Path, title: str) -> None:
    markdown = markdown_path.read_text(encoding="utf-8")
    body = markdown_to_plain_text(markdown) or title
    write_minimal_docx(docx_path, title=title, body=body)


def write_minimal_docx(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    paragraphs = "\n".join(_paragraph_xml(line) for line in [title, *body.splitlines()] if line.strip())
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {paragraphs}
    <w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>
"""
    with ZipFile(path, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", root_rels)
        docx.writestr("word/document.xml", document)


def _paragraph_xml(text: str) -> str:
    return f"<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"

