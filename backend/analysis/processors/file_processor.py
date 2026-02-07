"""
File processor for handling ZIP uploads and file extraction
"""
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import hashlib
from datetime import datetime


class FileProcessor:
    """Handles file uploads, ZIP extraction, and security validation"""

    # Security limits
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_EXTRACTED_SIZE = 100 * 1024 * 1024  # 100 MB (ZIP bomb protection)
    ALLOWED_EXTENSIONS = {".py", ".zip"}
    MAX_FILES_IN_ZIP = 1000

    def __init__(self, storage_path: str = "backend/storage/uploads"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def process_upload(
        self, file_content: bytes, filename: str, user_id: int
    ) -> dict:
        """
        Process uploaded file (Python file or ZIP)

        Args:
            file_content: Raw file bytes
            filename: Original filename
            user_id: User ID for isolation

        Returns:
            dict with:
                - upload_id: Unique upload identifier
                - extracted_path: Path to extracted files
                - file_list: List of Python files found
                - size: Total size in bytes

        Raises:
            ValueError: If file validation fails
        """
        # Validate file
        self._validate_file(file_content, filename)

        # Generate unique upload ID
        upload_id = self._generate_upload_id(user_id, filename)

        # Create user-specific directory
        user_upload_dir = self.storage_path / str(user_id) / upload_id
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        file_ext = Path(filename).suffix.lower()

        if file_ext == ".zip":
            # Extract ZIP
            extracted_path = await self._extract_zip(
                file_content, user_upload_dir, filename
            )
        else:
            # Single Python file
            extracted_path = user_upload_dir
            file_path = extracted_path / filename
            file_path.write_bytes(file_content)

        # Scan for Python files
        python_files = self._scan_python_files(extracted_path)

        # Calculate total size
        total_size = sum(f.stat().st_size for f in python_files)

        return {
            "upload_id": upload_id,
            "extracted_path": str(extracted_path),
            "file_list": [str(f.relative_to(extracted_path)) for f in python_files],
            "size": total_size,
            "file_count": len(python_files),
        }

    async def _extract_zip(
        self, file_content: bytes, target_dir: Path, filename: str
    ) -> Path:
        """
        Safely extract ZIP file with security checks

        Args:
            file_content: ZIP file bytes
            target_dir: Target extraction directory
            filename: Original filename

        Returns:
            Path to extracted files

        Raises:
            ValueError: If ZIP validation fails
        """
        # Write ZIP to temporary file
        temp_zip = target_dir / filename
        temp_zip.write_bytes(file_content)

        try:
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                # Security checks
                self._validate_zip(zip_ref)

                # Extract
                extract_dir = target_dir / "extracted"
                zip_ref.extractall(extract_dir)

                return extract_dir

        except zipfile.BadZipFile:
            raise ValueError(f"Invalid ZIP file: {filename}")
        finally:
            # Clean up temporary ZIP
            if temp_zip.exists():
                temp_zip.unlink()

    def _validate_file(self, file_content: bytes, filename: str):
        """
        Validate uploaded file

        Raises:
            ValueError: If validation fails
        """
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(file_content)} bytes "
                f"(max: {self.MAX_FILE_SIZE} bytes)"
            )

        # Check extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file type: {file_ext}. "
                f"Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Check for null bytes (potential exploit)
        if b'\x00' in file_content[:1024]:  # Check first KB
            raise ValueError("File contains null bytes (potential binary exploit)")

    def _validate_zip(self, zip_ref: zipfile.ZipFile):
        """
        Validate ZIP file for security threats

        Raises:
            ValueError: If validation fails
        """
        file_list = zip_ref.namelist()

        # Check number of files
        if len(file_list) > self.MAX_FILES_IN_ZIP:
            raise ValueError(
                f"ZIP contains too many files: {len(file_list)} "
                f"(max: {self.MAX_FILES_IN_ZIP})"
            )

        # Check total uncompressed size (ZIP bomb protection)
        total_size = sum(info.file_size for info in zip_ref.infolist())
        if total_size > self.MAX_EXTRACTED_SIZE:
            raise ValueError(
                f"ZIP uncompressed size too large: {total_size} bytes "
                f"(max: {self.MAX_EXTRACTED_SIZE} bytes)"
            )

        # Check for path traversal attacks
        for filename in file_list:
            # Normalize path
            normalized = Path(filename).resolve()

            # Check for absolute paths
            if Path(filename).is_absolute():
                raise ValueError(f"ZIP contains absolute path: {filename}")

            # Check for parent directory references
            if ".." in Path(filename).parts:
                raise ValueError(f"ZIP contains path traversal: {filename}")

    def _scan_python_files(self, directory: Path) -> List[Path]:
        """
        Recursively scan directory for Python files

        Args:
            directory: Directory to scan

        Returns:
            List of Python file paths
        """
        python_files = []

        for file_path in directory.rglob("*.py"):
            # Skip __pycache__ and hidden files
            if "__pycache__" in file_path.parts or file_path.name.startswith("."):
                continue

            python_files.append(file_path)

        return python_files

    def _generate_upload_id(self, user_id: int, filename: str) -> str:
        """
        Generate unique upload ID

        Args:
            user_id: User ID
            filename: Original filename

        Returns:
            Unique upload ID (hash)
        """
        timestamp = datetime.utcnow().isoformat()
        content = f"{user_id}:{filename}:{timestamp}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:16]

    def cleanup_upload(self, user_id: int, upload_id: str):
        """
        Clean up uploaded files

        Args:
            user_id: User ID
            upload_id: Upload ID to clean up
        """
        upload_dir = self.storage_path / str(user_id) / upload_id
        if upload_dir.exists():
            shutil.rmtree(upload_dir)

    def get_upload_path(self, user_id: int, upload_id: str) -> Optional[Path]:
        """
        Get path to uploaded files

        Args:
            user_id: User ID
            upload_id: Upload ID

        Returns:
            Path to upload directory or None if not found
        """
        upload_dir = self.storage_path / str(user_id) / upload_id
        if upload_dir.exists():
            return upload_dir
        return None
