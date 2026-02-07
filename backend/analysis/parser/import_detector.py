"""
Import detector for identifying UI framework imports
"""
import ast
from typing import Dict, List, Set
from analysis.models.analysis_models import Import


class ImportDetector:
    """Detects and classifies imports, focusing on UI frameworks"""

    # UI framework patterns
    UI_FRAMEWORKS: Dict[str, List[str]] = {
        "PyQt5": ["QtWidgets", "QtGui", "QtCore", "QtWebEngineWidgets", "uic"],
        "PyQt6": ["QtWidgets", "QtGui", "QtCore", "QtWebEngineWidgets", "uic"],
        "PySide2": ["QtWidgets", "QtGui", "QtCore", "QtWebEngineWidgets"],
        "PySide6": ["QtWidgets", "QtGui", "QtCore", "QtWebEngineWidgets"],
        "tkinter": ["*"],  # All tkinter imports are UI
        "wx": ["*"],  # wxPython
    }

    # Common UI class names (for detecting inheritance)
    UI_BASE_CLASSES: Set[str] = {
        "QWidget", "QMainWindow", "QDialog", "QFrame", "QScrollArea",
        "QPushButton", "QLabel", "QLineEdit", "QTextEdit", "QComboBox",
        "QCheckBox", "QRadioButton", "QSlider", "QProgressBar",
        "QTableWidget", "QListWidget", "QTreeWidget",
        "QGraphicsView", "QGraphicsScene", "QGraphicsItem",
        "Tk", "Frame", "Canvas", "Button", "Label",  # tkinter
    }

    def __init__(self):
        self.detected_imports: List[Import] = []

    def detect_imports(self, tree: ast.Module) -> List[Import]:
        """
        Detect all imports in an AST tree

        Args:
            tree: Parsed AST tree

        Returns:
            List of Import objects
        """
        self.detected_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._process_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._process_import_from(node)

        return self.detected_imports

    def _process_import(self, node: ast.Import):
        """Process 'import module' statements"""
        for alias in node.names:
            module_name = alias.name
            is_ui = self._is_ui_module(module_name)

            import_obj = Import(
                module=module_name,
                names=[alias.asname if alias.asname else module_name],
                is_ui=is_ui,
                line_number=node.lineno
            )
            self.detected_imports.append(import_obj)

    def _process_import_from(self, node: ast.ImportFrom):
        """Process 'from module import ...' statements"""
        if not node.module:
            return

        module_name = node.module
        imported_names = [alias.name for alias in node.names]
        is_ui = self._is_ui_import_from(module_name, imported_names)

        import_obj = Import(
            module=module_name,
            names=imported_names,
            is_ui=is_ui,
            line_number=node.lineno
        )
        self.detected_imports.append(import_obj)

    def _is_ui_module(self, module_name: str) -> bool:
        """
        Check if a module is a UI framework

        Args:
            module_name: Module name (e.g., 'PyQt5', 'tkinter')

        Returns:
            True if it's a UI framework
        """
        # Direct match
        if module_name in self.UI_FRAMEWORKS:
            return True

        # Check if it's a submodule (e.g., 'PyQt5.QtWidgets')
        for framework in self.UI_FRAMEWORKS.keys():
            if module_name.startswith(f"{framework}."):
                return True

        return False

    def _is_ui_import_from(self, module_name: str, imported_names: List[str]) -> bool:
        """
        Check if 'from module import ...' is a UI import

        Args:
            module_name: Module name
            imported_names: List of imported names

        Returns:
            True if it's a UI import
        """
        # Direct framework match
        if module_name in self.UI_FRAMEWORKS:
            return True

        # Check submodules
        for framework, submodules in self.UI_FRAMEWORKS.items():
            if module_name.startswith(f"{framework}."):
                # Check if importing from a UI submodule
                submodule_name = module_name.split(".", 1)[1] if "." in module_name else ""
                if "*" in submodules or submodule_name in submodules:
                    return True

        # Check if importing UI base classes directly
        if any(name in self.UI_BASE_CLASSES for name in imported_names):
            return True

        return False

    def has_ui_imports(self) -> bool:
        """Check if any UI imports were detected"""
        return any(imp.is_ui for imp in self.detected_imports)

    def get_ui_imports(self) -> List[Import]:
        """Get only UI framework imports"""
        return [imp for imp in self.detected_imports if imp.is_ui]

    def get_non_ui_imports(self) -> List[Import]:
        """Get non-UI imports"""
        return [imp for imp in self.detected_imports if not imp.is_ui]

    def get_ui_frameworks_used(self) -> Set[str]:
        """Get set of UI frameworks used in the file"""
        frameworks = set()
        for imp in self.get_ui_imports():
            for framework in self.UI_FRAMEWORKS.keys():
                if imp.module.startswith(framework):
                    frameworks.add(framework)
                    break
        return frameworks
