"""Storage abstraction for PDF SOP document files."""

import os
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union
from flask import current_app
from app.utils.errors import FileUploadError, NotFoundError
from app.utils.security import compute_sha256, sanitize_filename, validate_pdf_signature


class StorageService:
    """Handles secure file storage, integrity validation, and retrieval."""

    def __init__(self, base_path: Optional[str] = None):
        self._configured_path = base_path

    @property
    def base_dir(self) -> Path:
        """Resolve storage directory from configuration."""
        if self._configured_path:
            p = Path(self._configured_path).resolve()
        elif current_app:
            p = Path(current_app.config.get("DOCUMENT_STORAGE_PATH", "./data/documents")).resolve()
        else:
            p = Path("./data/documents").resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            if not p.exists():
                import tempfile
                p = Path(tempfile.gettempdir()) / "biztelai_docs"
                p.mkdir(parents=True, exist_ok=True)
        return p

    def save_file(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        max_size_bytes: Optional[int] = None,
    ) -> Tuple[str, str, int, str]:
        """Validate, hash, and persist uploaded PDF to disk.

        Returns:
            Tuple[stored_filename, original_filename, file_size_bytes, sha256_hash]
        """
        clean_name = sanitize_filename(original_filename)

        # Read first 1024 bytes to verify PDF magic header
        header = file_stream.read(1024)
        if not validate_pdf_signature(header):
            raise FileUploadError("Invalid file signature: uploaded file is not a valid PDF document.")

        # Read rest of file
        rest = file_stream.read()
        full_bytes = header + rest
        file_size = len(full_bytes)

        # Check maximum allowed size
        max_allowed = max_size_bytes or (
            current_app.config.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024) if current_app else 50 * 1024 * 1024
        )
        if file_size > max_allowed:
            raise FileUploadError(
                f"File size exceeds limit: {file_size / (1024*1024):.2f}MB > {max_allowed / (1024*1024):.1f}MB."
            )

        # Compute SHA-256 hash
        sha256_hash = compute_sha256(full_bytes)

        # Generate unique storage filename
        stored_filename = f"{uuid.uuid4().hex}_{clean_name}"
        destination = self.base_dir / stored_filename

        with open(destination, "wb") as f:
            f.write(full_bytes)

        return stored_filename, clean_name, file_size, sha256_hash

    def get_file_path(self, stored_filename: str) -> Path:
        """Retrieve absolute path to stored file with multi-path resolution and traversal check."""
        import tempfile
        clean_name = sanitize_filename(stored_filename)
        candidate_dirs = [
            self.base_dir,
            (Path(__file__).resolve().parent.parent.parent / "data" / "documents").resolve(),
            (Path(__file__).resolve().parent.parent.parent.parent / "data" / "documents").resolve(),
            (Path(__file__).resolve().parent.parent.parent / "BiztelAI-Backend" / "data" / "documents").resolve(),
            (Path.cwd() / "data" / "documents").resolve(),
            (Path.cwd() / "BiztelAI-Backend" / "data" / "documents").resolve(),
            Path(tempfile.gettempdir()) / "biztelai_docs",
        ]

        # 1. Direct exact filename check
        for d in candidate_dirs:
            if d.exists():
                target = (d / clean_name).resolve()
                if target.exists() and target.is_file():
                    return target

        # 2. Suffix or stem match (in case stored_filename has uuid or original filename)
        for d in candidate_dirs:
            if d.exists():
                for f in d.iterdir():
                    if f.is_file() and (f.name == clean_name or f.name.endswith(clean_name) or clean_name.endswith(f.name)):
                        return f

        raise NotFoundError(f"Document file not found: {stored_filename}")

    def delete_file(self, stored_filename: str) -> bool:
        """Remove file from storage if it exists."""
        try:
            path = self.get_file_path(stored_filename)
            if path.exists():
                os.remove(path)
                return True
        except NotFoundError:
            pass
        return False

