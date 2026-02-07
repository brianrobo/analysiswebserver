"""
Data Processing Module - Pure Logic
This file contains business logic with no UI dependencies
"""
import csv
from typing import List, Dict, Any


def process_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and parse CSV file

    Args:
        file_path: Path to CSV file

    Returns:
        List of dictionaries representing rows
    """
    data = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    return data


def calculate_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for dataset

    Args:
        data: List of data rows

    Returns:
        Dictionary with statistics
    """
    if not data:
        return {
            "row_count": 0,
            "column_count": 0,
            "mean": 0.0,
            "total": 0.0,
        }

    row_count = len(data)
    column_count = len(data[0].keys()) if data else 0

    # Calculate numeric statistics (assumes 'value' column exists)
    numeric_values = []
    for row in data:
        value = row.get('value', '0')
        try:
            numeric_values.append(float(value))
        except ValueError:
            pass

    mean = sum(numeric_values) / len(numeric_values) if numeric_values else 0.0
    total = sum(numeric_values)

    return {
        "row_count": row_count,
        "column_count": column_count,
        "mean": mean,
        "total": total,
    }


def filter_data(data: List[Dict[str, Any]], key: str, value: Any) -> List[Dict[str, Any]]:
    """
    Filter data by key-value pair

    Args:
        data: List of data rows
        key: Key to filter on
        value: Value to match

    Returns:
        Filtered list
    """
    return [row for row in data if row.get(key) == value]


def sort_data(data: List[Dict[str, Any]], key: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """
    Sort data by key

    Args:
        data: List of data rows
        key: Key to sort by
        reverse: Sort in descending order if True

    Returns:
        Sorted list
    """
    return sorted(data, key=lambda x: x.get(key, ''), reverse=reverse)


def validate_data(data: List[Dict[str, Any]], required_columns: List[str]) -> bool:
    """
    Validate that data has required columns

    Args:
        data: List of data rows
        required_columns: List of required column names

    Returns:
        True if valid, False otherwise
    """
    if not data:
        return False

    first_row = data[0]
    return all(col in first_row for col in required_columns)
