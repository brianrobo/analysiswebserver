"""
Analysis Module - Mixed UI and Logic
This file contains both UI-dependent and pure functions
"""
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from typing import List, Dict, Any
import os


# Pure functions (no UI dependencies)

def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numbers - Pure function"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def find_outliers(numbers: List[float], threshold: float = 2.0) -> List[float]:
    """Find outliers in dataset - Pure function"""
    if not numbers:
        return []

    mean = calculate_average(numbers)
    std_dev = (sum((x - mean) ** 2 for x in numbers) / len(numbers)) ** 0.5

    outliers = [x for x in numbers if abs(x - mean) > threshold * std_dev]
    return outliers


def normalize_data(numbers: List[float]) -> List[float]:
    """Normalize data to 0-1 range - Pure function"""
    if not numbers:
        return []

    min_val = min(numbers)
    max_val = max(numbers)

    if max_val == min_val:
        return [0.5] * len(numbers)

    return [(x - min_val) / (max_val - min_val) for x in numbers]


# Mixed functions (has UI dependencies)

def analyze_and_show_results(data: List[Dict[str, Any]], parent=None) -> Dict[str, Any]:
    """
    Analyze data and show results in message box
    Mixed function - has UI dependency
    """
    # Pure calculation
    row_count = len(data)
    numeric_values = []

    for row in data:
        value = row.get('value', '0')
        try:
            numeric_values.append(float(value))
        except ValueError:
            pass

    avg = calculate_average(numeric_values)
    outliers = find_outliers(numeric_values)

    # UI interaction
    result_text = f"Rows: {row_count}\\n"
    result_text += f"Average: {avg:.2f}\\n"
    result_text += f"Outliers: {len(outliers)}"

    if parent:
        QMessageBox.information(parent, "Analysis Results", result_text)

    return {
        "row_count": row_count,
        "average": avg,
        "outlier_count": len(outliers),
    }


def export_results(data: Dict[str, Any], parent=None) -> bool:
    """
    Export results to file with file dialog
    Mixed function - has UI dependency
    """
    # UI interaction for file selection
    if parent:
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Results",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
    else:
        file_path = "results.json"

    if not file_path:
        return False

    # Pure file writing
    import json
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        if parent:
            QMessageBox.critical(parent, "Error", f"Export failed: {str(e)}")
        return False


def validate_file_path(file_path: str, show_error: bool = True, parent=None) -> bool:
    """
    Validate file path and optionally show error
    Mixed function - has optional UI dependency
    """
    # Pure validation
    if not file_path:
        if show_error and parent:
            QMessageBox.warning(parent, "Warning", "File path is empty")
        return False

    if not os.path.exists(file_path):
        if show_error and parent:
            QMessageBox.warning(parent, "Warning", f"File not found: {file_path}")
        return False

    return True
