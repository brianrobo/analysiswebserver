"""
Sample PyQt5 Main Window - UI File
This file is predominantly UI code
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from data_processor import process_csv_data, calculate_statistics


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.data = None

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Data Analysis Tool")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()

        # Title label
        title = QLabel("PyQt Data Analysis Tool")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # File path input
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Enter file path...")
        layout.addWidget(self.file_path_input)

        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(browse_btn)

        # Analyze button
        analyze_btn = QPushButton("Analyze Data")
        analyze_btn.clicked.connect(self.analyze_data)
        layout.addWidget(analyze_btn)

        # Result label
        self.result_label = QLabel("Results will appear here")
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        central_widget.setLayout(layout)

    def browse_file(self):
        """Open file dialog to select CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def analyze_data(self):
        """Analyze selected file"""
        file_path = self.file_path_input.text()

        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file first")
            return

        try:
            # Use pure logic function
            self.data = process_csv_data(file_path)

            # Calculate statistics
            stats = calculate_statistics(self.data)

            # Display results
            result_text = f"Rows: {stats['row_count']}\\n"
            result_text += f"Columns: {stats['column_count']}\\n"
            result_text += f"Mean: {stats['mean']:.2f}\\n"

            self.result_label.setText(result_text)

            QMessageBox.information(self, "Success", "Analysis completed!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About",
            "Data Analysis Tool v1.0\\nBuilt with PyQt5"
        )
