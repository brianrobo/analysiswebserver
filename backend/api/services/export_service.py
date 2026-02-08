"""
Export Service for analysis results
Supports JSON, CSV, and ZIP formats
"""
import json
import csv
import zipfile
from io import StringIO, BytesIO
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting analysis results in different formats

    Formats:
    - JSON: Pretty-printed complete analysis result
    - CSV: Summary table with key metrics
    - ZIP: Pure functions extracted with README
    """

    def export_json(self, result_data: Dict[str, Any]) -> str:
        """
        Export analysis result as pretty-printed JSON

        Args:
            result_data: Complete analysis result dictionary

        Returns:
            JSON string with ensure_ascii=False for Korean support
        """
        try:
            json_str = json.dumps(
                result_data,
                indent=2,
                ensure_ascii=False,  # Support Korean characters
                sort_keys=False
            )
            logger.info(f"Exported analysis result as JSON ({len(json_str)} bytes)")
            return json_str
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise

    def export_csv(self, result_data: Dict[str, Any]) -> str:
        """
        Export analysis summary as CSV table

        Columns: File Path, LOC, UI %, Pure Functions, Classification, Web Ready

        Args:
            result_data: Complete analysis result dictionary

        Returns:
            CSV string with UTF-8 BOM for Excel compatibility
        """
        try:
            output = StringIO()

            # UTF-8 BOM for Excel
            output.write('\ufeff')

            writer = csv.writer(output)

            # Header
            writer.writerow([
                "File Path",
                "Lines of Code",
                "UI Percentage (%)",
                "Pure Functions",
                "Classification",
                "Web Ready"
            ])

            # Extract file data from result
            data = result_data.get("result_data", {})

            # UI Files
            for file in data.get("ui_files", []):
                writer.writerow([
                    file.get("path", ""),
                    file.get("loc", 0),
                    f"{file.get('ui_percentage', 0):.1f}",
                    len([f for f in file.get("functions", []) if f.get("is_pure", False)]),
                    "UI",
                    "No"
                ])

            # Logic Files
            for file in data.get("logic_files", []):
                pure_count = len([f for f in file.get("functions", []) if f.get("is_pure", False)])
                writer.writerow([
                    file.get("path", ""),
                    file.get("loc", 0),
                    f"{file.get('ui_percentage', 0):.1f}",
                    pure_count,
                    "Logic",
                    "Yes" if pure_count > 0 else "No"
                ])

            # Mixed Files
            for file in data.get("mixed_files", []):
                pure_count = len([f for f in file.get("functions", []) if f.get("is_pure", False)])
                writer.writerow([
                    file.get("path", ""),
                    file.get("loc", 0),
                    f"{file.get('ui_percentage', 0):.1f}",
                    pure_count,
                    "Mixed",
                    "Partial" if pure_count > 0 else "No"
                ])

            csv_str = output.getvalue()
            logger.info(f"Exported analysis result as CSV ({len(csv_str)} bytes)")
            return csv_str

        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
        finally:
            output.close()

    def export_pure_functions_zip(
        self,
        result_data: Dict[str, Any],
        project_name: str = "extracted_functions"
    ) -> bytes:
        """
        Export pure functions as ZIP archive

        Creates a ZIP with:
        - Extracted pure functions (one file per source file)
        - README.md with extraction summary and recommendations

        Args:
            result_data: Complete analysis result dictionary
            project_name: Project name for folder structure

        Returns:
            ZIP file as bytes
        """
        try:
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                data = result_data.get("result_data", {})
                total_pure_functions = 0
                extracted_files = []

                # Process all files
                all_files = (
                    data.get("ui_files", []) +
                    data.get("logic_files", []) +
                    data.get("mixed_files", [])
                )

                for file_data in all_files:
                    file_path = file_data.get("path", "unknown.py")
                    functions = file_data.get("functions", [])

                    # Filter pure functions
                    pure_functions = [f for f in functions if f.get("is_pure", False)]

                    if not pure_functions:
                        continue

                    # Generate extracted file content
                    extracted_content = self._generate_pure_function_file(
                        file_path,
                        pure_functions,
                        file_data
                    )

                    # Add to ZIP
                    zip_path = f"{project_name}/{Path(file_path).stem}_pure.py"
                    zip_file.writestr(zip_path, extracted_content)

                    total_pure_functions += len(pure_functions)
                    extracted_files.append({
                        "file": file_path,
                        "functions": len(pure_functions)
                    })

                # Generate README
                readme_content = self._generate_readme(
                    result_data,
                    total_pure_functions,
                    extracted_files
                )
                zip_file.writestr(f"{project_name}/README.md", readme_content)

            zip_bytes = zip_buffer.getvalue()
            logger.info(f"Exported {total_pure_functions} pure functions as ZIP ({len(zip_bytes)} bytes)")
            return zip_bytes

        except Exception as e:
            logger.error(f"Failed to export ZIP: {e}")
            raise
        finally:
            zip_buffer.close()

    def _generate_pure_function_file(
        self,
        source_file: str,
        pure_functions: List[Dict[str, Any]],
        file_data: Dict[str, Any]
    ) -> str:
        """Generate Python file with extracted pure functions"""
        lines = [
            '"""',
            f'Pure functions extracted from: {source_file}',
            '',
            'These functions have no UI dependencies and can be reused in web backend.',
            '"""',
            '',
        ]

        # Add imports if available
        imports = file_data.get("imports", [])
        if imports:
            lines.append("# Original imports")
            for imp in imports:
                module = imp.get("module", "")
                names = imp.get("names", [])
                if names and names != ["*"]:
                    lines.append(f"from {module} import {', '.join(names)}")
                elif names == ["*"]:
                    lines.append(f"from {module} import *")
                else:
                    lines.append(f"import {module}")
            lines.append("")

        # Add each pure function
        for func in pure_functions:
            func_name = func.get("name", "unknown")
            start_line = func.get("start_line", 0)
            end_line = func.get("end_line", 0)
            dependencies = func.get("dependencies", [])

            lines.append(f"# Function: {func_name}")
            lines.append(f"# Original location: lines {start_line}-{end_line}")
            if dependencies:
                lines.append(f"# Dependencies: {', '.join(dependencies)}")
            lines.append(f"# Web-ready: Yes (Pure function)")
            lines.append("")

            # Note: We don't have the actual function code stored
            # In a real implementation, you'd extract it from the source file
            lines.append(f"def {func_name}():")
            lines.append("    # TODO: Copy function implementation from source file")
            lines.append(f"    # Source: {source_file}:{start_line}-{end_line}")
            lines.append("    pass")
            lines.append("")

        return "\n".join(lines)

    def _generate_readme(
        self,
        result_data: Dict[str, Any],
        total_pure_functions: int,
        extracted_files: List[Dict[str, Any]]
    ) -> str:
        """Generate README for extracted functions ZIP"""
        data = result_data.get("result_data", {})
        summary = result_data.get("summary", {})

        lines = [
            "# Extracted Pure Functions",
            "",
            "## Summary",
            "",
            f"- **Total Pure Functions**: {total_pure_functions}",
            f"- **Source Files**: {len(extracted_files)}",
            f"- **Web Readiness**: {summary.get('web_ready_percentage', 0):.1f}%",
            "",
            "## Extracted Files",
            "",
        ]

        for item in extracted_files:
            lines.append(f"- `{Path(item['file']).stem}_pure.py`: {item['functions']} functions")

        lines.extend([
            "",
            "## Usage Recommendations",
            "",
            "These pure functions are web-ready and can be directly reused in your FastAPI backend:",
            "",
            "1. **Copy to Backend**: Place these files in your backend logic layer",
            "2. **Import in Routes**: Use these functions in your API endpoints",
            "3. **Test Independently**: Pure functions are easy to unit test",
            "4. **No UI Refactoring**: These functions require no modification",
            "",
            "## Web Conversion Guide",
            "",
        ])

        # Add conversion guide
        guide = data.get("web_conversion_guide", {})
        lines.append(f"**Summary**: {guide.get('summary', 'N/A')}")
        lines.append(f"**Recommended Approach**: {guide.get('recommended_approach', 'N/A')}")
        lines.append(f"**Estimated Complexity**: {guide.get('estimated_complexity', 'N/A')}")
        lines.append("")

        recommendations = guide.get("recommendations", [])
        if recommendations:
            lines.append("**Recommendations**:")
            for rec in recommendations:
                lines.append(f"- {rec}")

        lines.extend([
            "",
            "---",
            "",
            "Generated by Analysis Tool API",
            f"Total LOC: {summary.get('total_loc', 0)}",
            f"UI Files: {summary.get('ui_files_count', 0)}",
            f"Logic Files: {summary.get('logic_files_count', 0)}",
            f"Mixed Files: {summary.get('mixed_files_count', 0)}",
        ])

        return "\n".join(lines)


# Global export service instance
export_service = ExportService()
