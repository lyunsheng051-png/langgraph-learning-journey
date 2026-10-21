"""格式解析放在辅助模块，图只处理路由和统一结果。"""

from io import BytesIO
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from lxml.etree import XMLSyntaxError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from chapter_demo.state import TextSection


MAX_FILE_BYTES = 1024 * 1024
MAX_TEXT_CHARACTERS = 100_000
MAX_PDF_PAGES = 20
MAX_DOCX_EXPANDED_BYTES = 8 * 1024 * 1024


class ExtractionError(ValueError):
    """可预期的输入或格式问题，由图转入结束路径。"""


def read_bytes(path: Path) -> bytes:
    with path.open("rb") as source:
        data = source.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ExtractionError("文件超过本章的 1 MiB 上限。")
    return data


def validate_sections(sections: list[TextSection]) -> list[TextSection]:
    if sum(len(section["text"]) for section in sections) > MAX_TEXT_CHARACTERS:
        raise ExtractionError("提取文本超过本章的 100,000 字符上限。")
    return sections


def extract_txt(path: Path) -> list[TextSection]:
    try:
        text = read_bytes(path).decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ExtractionError("TXT 不是有效的 UTF-8 文本，请先另存为 UTF-8。") from error
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    return validate_sections([
        {"location": f"第 {index} 段", "text": paragraph}
        for index, paragraph in enumerate(paragraphs, start=1)
    ])


def extract_docx(path: Path) -> list[TextSection]:
    data = read_bytes(path)
    try:
        with ZipFile(BytesIO(data)) as archive:
            if sum(item.file_size for item in archive.infolist()) > MAX_DOCX_EXPANDED_BYTES:
                raise ExtractionError("DOCX 解压内容超过本章的 8 MiB 上限。")
        document = Document(BytesIO(data))
        sections = [
            {"location": f"第 {index} 段", "text": paragraph.text.strip()}
            for index, paragraph in enumerate(document.paragraphs, start=1)
            if paragraph.text.strip()
        ]
    except (BadZipFile, PackageNotFoundError, KeyError, XMLSyntaxError) as error:
        raise ExtractionError("无法解析 DOCX，请检查文件内容是否完整且格式正确。") from error
    return validate_sections(sections)


def extract_pdf(path: Path) -> list[TextSection]:
    data = read_bytes(path)
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ExtractionError("PDF 已加密，本章不处理加密文件。")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ExtractionError("PDF 超过本章的 20 页上限。")
        sections = []
        for number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                sections.append({"location": f"第 {number} 页", "text": text})
    except PdfReadError as error:
        raise ExtractionError("无法解析 PDF，请检查文件内容是否完整且格式正确。") from error
    return validate_sections(sections)
