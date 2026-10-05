from pathlib import Path

from django.conf import settings

ALLOWED = {".pdf": "pdf", ".docx": "docx"}


class FileValidationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def validate_upload(f) -> str:
    """Server-side checks; client filename/Content-Type are NOT trusted. Returns 'pdf' or 'docx'."""
    ext = Path(f.name or "").suffix.lower()
    if ext not in ALLOWED:
        raise FileValidationError("UNSUPPORTED_FILE", "Unsupported file format. Upload a PDF or DOCX.")
    if f.size == 0:
        raise FileValidationError("EMPTY_FILE", "The file is empty.")
    if f.size > settings.MAX_UPLOAD_SIZE:
        raise FileValidationError("FILE_TOO_LARGE", f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB).")
    head = f.read(8)
    f.seek(0)
    kind = ALLOWED[ext]
    # magic bytes: PDF starts with %PDF, DOCX is a ZIP container (PK)
    if kind == "pdf" and not head.startswith(b"%PDF"):
        raise FileValidationError("INVALID_FILE", "The file content is not a valid PDF.")
    if kind == "docx" and not head.startswith(b"PK"):
        raise FileValidationError("INVALID_FILE", "The file content is not a valid DOCX.")
    return kind
