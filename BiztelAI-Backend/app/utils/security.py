"""Security utilities: password hashing, file sanitization, PDF verification, hashing."""

import hashlib
import re
from pathlib import Path
from typing import Union
import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename to prevent directory traversal and injection attacks."""
    if not filename:
        return "unnamed_document.pdf"
    # Extract only the base name (strip directory parts)
    clean = Path(filename).name
    # Replace dangerous characters with underscores
    clean = re.sub(r"[^\w\s\.-]", "_", clean).strip()
    # Collapse multiple dots or spaces
    clean = re.sub(r"\.{2,}", ".", clean)
    clean = re.sub(r"\s+", "_", clean)
    if not clean.lower().endswith(".pdf"):
        clean += ".pdf"
    return clean or "document.pdf"


def validate_pdf_signature(header_bytes: bytes) -> bool:
    """Validate that file starts with valid PDF magic bytes '%PDF-'."""
    if not header_bytes or len(header_bytes) < 5:
        return False
    # PDF magic signature is %PDF- (0x25 0x50 0x44 0x46 0x2D)
    return header_bytes[:5] == b"%PDF-"


def compute_sha256(data: Union[bytes, Path, str]) -> str:
    """Compute SHA-256 hash of bytes or a file on disk."""
    hasher = hashlib.sha256()
    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    else:
        hasher.update(data)
    return hasher.hexdigest()


def mask_secret(secret: str, prefix_len: int = 4, suffix_len: int = 4) -> str:
    """Safely mask API keys or secrets for safe logging/display."""
    if not secret:
        return "<EMPTY>"
    if len(secret) <= (prefix_len + suffix_len):
        return "***"
    return f"{secret[:prefix_len]}...{secret[-suffix_len:]}"

