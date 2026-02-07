"""
Path processor for analyzing local Python projects
"""
from pathlib import Path
from typing import List, Optional


class PathProcessor:
    """Handles local directory path processing and validation"""

    # Security settings
    MAX_FILES = 1000  # Maximum files to analyze
    MAX_DEPTH = 10  # Maximum directory depth

    def __init__(self):
        pass

    def process_local_path(self, path: str) -> dict:
        """
        Process a local directory or file path

        Args:
            path: Local file system path

        Returns:
            dict with:
                - path: Validated path
                - file_list: List of Python files found
                - size: Total size in bytes
                - file_count: Number of Python files

        Raises:
            ValueError: If path validation fails
            FileNotFoundError: If path doesn't exist
        """
        # Validate and normalize path
        validated_path = self._validate_path(path)

        # Scan for Python files
        if validated_path.is_file():
            # Single file
            if validated_path.suffix.lower() != ".py":
                raise ValueError(f"Not a Python file: {validated_path}")
            python_files = [validated_path]
        else:
            # Directory
            python_files = self._scan_python_files(validated_path)

        if not python_files:
            raise ValueError(f"No Python files found in: {path}")

        # Calculate total size
        total_size = sum(f.stat().st_size for f in python_files)

        return {
            "path": str(validated_path),
            "file_list": [str(f) for f in python_files],
            "size": total_size,
            "file_count": len(python_files),
        }

    def _validate_path(self, path: str) -> Path:
        """
        Validate and normalize path

        Args:
            path: Path string

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If path doesn't exist
        """
        # Convert to Path
        path_obj = Path(path)

        # Check if exists
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        # Resolve to absolute path (removes .., ., etc.)
        try:
            resolved_path = path_obj.resolve(strict=True)
        except (RuntimeError, OSError) as e:
            raise ValueError(f"Invalid path: {path} ({e})")

        # Security: Check for symlink loops
        if resolved_path.is_symlink():
            raise ValueError(f"Symlinks are not allowed: {path}")

        # Security: Ensure it's a valid location (not system directories)
        self._check_restricted_paths(resolved_path)

        return resolved_path

    def _check_restricted_paths(self, path: Path):
        """
        Check if path is in restricted system directories

        Args:
            path: Path to check

        Raises:
            ValueError: If path is restricted
        """
        # List of restricted directories (Windows and Unix)
        restricted = [
            "/etc",
            "/sys",
            "/proc",
            "/dev",
            "/boot",
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ]

        path_str = str(path).lower()

        for restricted_dir in restricted:
            if path_str.startswith(restricted_dir.lower()):
                raise ValueError(
                    f"Access to system directories is restricted: {path}"
                )

    def _scan_python_files(self, directory: Path) -> List[Path]:
        """
        Recursively scan directory for Python files

        Args:
            directory: Directory to scan

        Returns:
            List of Python file paths

        Raises:
            ValueError: If too many files or too deep
        """
        python_files = []
        depth_count = {}

        for file_path in directory.rglob("*.py"):
            # Skip __pycache__ and hidden files
            if "__pycache__" in file_path.parts or file_path.name.startswith("."):
                continue

            # Check depth
            relative = file_path.relative_to(directory)
            depth = len(relative.parts) - 1  # -1 because file itself doesn't count
            depth_count[depth] = depth_count.get(depth, 0) + 1

            if depth > self.MAX_DEPTH:
                raise ValueError(
                    f"Directory structure too deep (max: {self.MAX_DEPTH} levels)"
                )

            python_files.append(file_path)

            # Check file count
            if len(python_files) > self.MAX_FILES:
                raise ValueError(
                    f"Too many Python files (max: {self.MAX_FILES}, found: {len(python_files)}+)"
                )

        return python_files

    def get_relative_path(self, file_path: Path, base_path: Path) -> str:
        """
        Get relative path from base

        Args:
            file_path: File path
            base_path: Base directory path

        Returns:
            Relative path string
        """
        try:
            return str(file_path.relative_to(base_path))
        except ValueError:
            # If not relative, return absolute
            return str(file_path)

    def get_project_name(self, path: Path) -> str:
        """
        Extract project name from path

        Args:
            path: Project path

        Returns:
            Project name (directory name or file name without extension)
        """
        if path.is_file():
            return path.stem
        else:
            return path.name
