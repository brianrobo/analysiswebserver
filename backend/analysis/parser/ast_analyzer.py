"""
AST-based Python code analyzer for extracting structure and dependencies
"""
import ast
from pathlib import Path
from typing import List, Set, Optional
from analysis.models.analysis_models import (
    Import,
    FunctionInfo,
    ClassInfo,
    FileAnalysis,
)
from analysis.parser.import_detector import ImportDetector


class ASTAnalyzer:
    """Analyzes Python files using AST to extract structure and dependencies"""

    def __init__(self):
        self.import_detector = ImportDetector()
        self.ui_frameworks: Set[str] = set()

    def analyze_file(self, file_path: str, content: Optional[str] = None) -> FileAnalysis:
        """
        Analyze a Python file and return structured analysis

        Args:
            file_path: Path to the Python file
            content: Optional file content (if None, reads from file_path)

        Returns:
            FileAnalysis object with complete analysis
        """
        if content is None:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # Parse AST
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            # Return empty analysis for files with syntax errors
            return FileAnalysis(
                path=file_path,
                imports=[],
                classes=[],
                functions=[],
                loc=len(content.splitlines()),
                is_ui_file=False,
                is_logic_file=False,
                is_mixed_file=False,
                ui_percentage=0.0,
            )

        # Detect imports
        imports = self.import_detector.detect_imports(tree)
        self.ui_frameworks = self.import_detector.get_ui_frameworks_used()

        # Extract classes
        classes = self._extract_classes(tree)

        # Extract top-level functions
        functions = self._extract_functions(tree)

        # Calculate metrics
        loc = len(content.splitlines())
        is_ui_file, is_logic_file, is_mixed_file, ui_percentage = self._classify_file(
            imports, classes, functions
        )

        return FileAnalysis(
            path=file_path,
            imports=imports,
            classes=classes,
            functions=functions,
            loc=loc,
            is_ui_file=is_ui_file,
            is_logic_file=is_logic_file,
            is_mixed_file=is_mixed_file,
            ui_percentage=ui_percentage,
        )

    def _extract_classes(self, tree: ast.Module) -> List[ClassInfo]:
        """Extract all class definitions from the AST"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get base class names
                bases = [self._get_name(base) for base in node.bases]

                # Check if it's a UI class
                is_ui_class = any(
                    base in self.import_detector.UI_BASE_CLASSES for base in bases
                )

                # Extract methods
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        method_info = self._analyze_function(item, is_method=True)
                        methods.append(method_info)

                # Calculate class LOC
                loc = self._calculate_node_loc(node)
                start_line = node.lineno
                end_line = node.end_lineno or start_line

                class_info = ClassInfo(
                    name=node.name,
                    bases=bases,
                    is_ui_class=is_ui_class,
                    methods=methods,
                    loc=loc,
                    start_line=start_line,
                    end_line=end_line,
                )
                classes.append(class_info)

        return classes

    def _extract_functions(self, tree: ast.Module) -> List[FunctionInfo]:
        """Extract top-level functions from the AST"""
        functions = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_info = self._analyze_function(node, is_method=False)
                functions.append(func_info)

        return functions

    def _analyze_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_method: bool
    ) -> FunctionInfo:
        """
        Analyze a function/method node

        Args:
            node: AST FunctionDef or AsyncFunctionDef node
            is_method: True if this is a class method

        Returns:
            FunctionInfo object
        """
        # Calculate LOC
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        loc = end_line - start_line + 1

        # Detect UI usage
        ui_usage = self._detect_ui_usage(node)

        # Detect dependencies (function calls)
        dependencies = self._detect_dependencies(node)

        # Check for global access
        has_global_access = self._has_global_access(node)

        # Determine if function is pure (no UI, no global state)
        is_pure = len(ui_usage) == 0 and not has_global_access and not is_method

        return FunctionInfo(
            name=node.name,
            start_line=start_line,
            end_line=end_line,
            loc=loc,
            is_pure=is_pure,
            ui_usage=ui_usage,
            dependencies=dependencies,
            has_global_access=has_global_access,
        )

    def _detect_ui_usage(self, node: ast.AST) -> List[str]:
        """Detect UI framework usage within a function/method"""
        ui_usage = []

        for child in ast.walk(node):
            # Check for UI class instantiation (e.g., QWidget())
            if isinstance(child, ast.Call):
                func_name = self._get_name(child.func)
                if func_name in self.import_detector.UI_BASE_CLASSES:
                    ui_usage.append(func_name)

            # Check for UI method calls (e.g., self.show())
            if isinstance(child, ast.Attribute):
                attr_name = child.attr
                # Common UI methods
                ui_methods = {
                    "show", "hide", "close", "exec", "exec_",
                    "setText", "setEnabled", "setVisible",
                    "addWidget", "setLayout", "setCentralWidget",
                }
                if attr_name in ui_methods:
                    ui_usage.append(f".{attr_name}()")

        return list(set(ui_usage))  # Remove duplicates

    def _detect_dependencies(self, node: ast.AST) -> List[str]:
        """Detect function calls (dependencies) within a function"""
        dependencies = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_name(child.func)
                if func_name and not func_name.startswith("_"):  # Skip private
                    dependencies.append(func_name)

        return list(set(dependencies))[:10]  # Return up to 10 unique dependencies

    def _has_global_access(self, node: ast.AST) -> bool:
        """Check if function accesses global variables"""
        for child in ast.walk(node):
            if isinstance(child, ast.Global) or isinstance(child, ast.Nonlocal):
                return True
        return False

    def _classify_file(
        self, imports: List[Import], classes: List[ClassInfo], functions: List[FunctionInfo]
    ) -> tuple[bool, bool, bool, float]:
        """
        Classify file as UI, Logic, or Mixed

        Returns:
            (is_ui_file, is_logic_file, is_mixed_file, ui_percentage)
        """
        # Check if file has UI imports
        has_ui_imports = any(imp.is_ui for imp in imports)

        # Check if file has UI classes
        has_ui_classes = any(cls.is_ui_class for cls in classes)

        # Count UI-dependent functions
        ui_functions = [f for f in functions if len(f.ui_usage) > 0]

        # Count pure functions
        pure_functions = [f for f in functions if f.is_pure]

        # Calculate total elements
        total_elements = len(classes) + len(functions)
        if total_elements == 0:
            # File with only imports or empty
            return has_ui_imports, not has_ui_imports, False, 0.0

        # Calculate UI percentage
        ui_elements = sum(
            [
                1 for cls in classes if cls.is_ui_class
            ] + [
                1 for func in functions if len(func.ui_usage) > 0
            ]
        )
        ui_percentage = (ui_elements / total_elements) * 100

        # Classification logic
        if ui_percentage >= 80:
            # Predominantly UI
            return True, False, False, ui_percentage
        elif ui_percentage <= 20 and len(pure_functions) > 0:
            # Predominantly logic
            return False, True, False, ui_percentage
        else:
            # Mixed
            return False, False, True, ui_percentage

    def _get_name(self, node: ast.AST) -> str:
        """Extract name from various AST node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # For nested attributes like PyQt5.QtWidgets.QWidget
            parent = self._get_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return ""

    def _calculate_node_loc(self, node: ast.AST) -> int:
        """Calculate lines of code for an AST node"""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            return (node.end_lineno or node.lineno) - node.lineno + 1
        return 0
