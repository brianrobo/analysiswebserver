"""
Core analysis engine that orchestrates the entire analysis process
"""
from pathlib import Path
from typing import List, Optional
from analysis.models.analysis_models import (
    ProjectAnalysisResult,
    FileAnalysis,
    ExtractionSuggestion,
    RefactoringSuggestion,
    WebConversionGuide,
)
from analysis.parser.ast_analyzer import ASTAnalyzer
from analysis.processors.path_processor import PathProcessor


class AnalysisEngine:
    """Main analysis engine that coordinates all analysis components"""

    def __init__(self):
        self.ast_analyzer = ASTAnalyzer()
        self.path_processor = PathProcessor()

    async def analyze_project(
        self, project_path: str, project_name: Optional[str] = None
    ) -> ProjectAnalysisResult:
        """
        Analyze a complete Python project

        Args:
            project_path: Path to project directory or extracted files
            project_name: Optional project name (auto-detected if None)

        Returns:
            ProjectAnalysisResult with complete analysis
        """
        path_obj = Path(project_path)

        # Auto-detect project name
        if project_name is None:
            project_name = self.path_processor.get_project_name(path_obj)

        # Get list of Python files
        if path_obj.is_file():
            python_files = [path_obj]
        else:
            python_files = list(path_obj.rglob("*.py"))
            # Filter out __pycache__
            python_files = [
                f for f in python_files
                if "__pycache__" not in f.parts and not f.name.startswith(".")
            ]

        # Analyze each file
        file_analyses: List[FileAnalysis] = []
        for file_path in python_files:
            try:
                analysis = self.ast_analyzer.analyze_file(str(file_path))
                file_analyses.append(analysis)
            except Exception as e:
                # Log error but continue with other files
                print(f"Error analyzing {file_path}: {e}")
                continue

        # Classify files
        ui_files = [f for f in file_analyses if f.is_ui_file]
        logic_files = [f for f in file_analyses if f.is_logic_file]
        mixed_files = [f for f in file_analyses if f.is_mixed_file]

        # Generate extraction suggestions
        extraction_suggestions = self._generate_extraction_suggestions(file_analyses)

        # Generate refactoring suggestions
        refactoring_suggestions = self._generate_refactoring_suggestions(file_analyses)

        # Generate web conversion guide
        web_conversion_guide = self._generate_web_conversion_guide(
            ui_files, logic_files, mixed_files
        )

        # Create summary
        analysis_summary = {
            "total_loc": sum(f.loc for f in file_analyses),
            "ui_files_count": len(ui_files),
            "logic_files_count": len(logic_files),
            "mixed_files_count": len(mixed_files),
            "total_classes": sum(len(f.classes) for f in file_analyses),
            "total_functions": sum(len(f.functions) for f in file_analyses),
            "ui_frameworks": list(self.ast_analyzer.ui_frameworks),
            "web_ready_percentage": self._calculate_web_ready_percentage(file_analyses),
        }

        return ProjectAnalysisResult(
            project_name=project_name,
            total_files=len(file_analyses),
            analysis_summary=analysis_summary,
            ui_files=ui_files,
            logic_files=logic_files,
            mixed_files=mixed_files,
            extraction_suggestions=extraction_suggestions,
            refactoring_suggestions=refactoring_suggestions,
            web_conversion_guide=web_conversion_guide,
        )

    def _generate_extraction_suggestions(
        self, file_analyses: List[FileAnalysis]
    ) -> List[ExtractionSuggestion]:
        """Generate suggestions for extracting pure logic functions"""
        suggestions = []

        for file in file_analyses:
            # Only process mixed files
            if not file.is_mixed_file:
                continue

            # Look for pure functions
            for func in file.functions:
                if func.is_pure and func.loc >= 3:  # At least 3 lines
                    suggestion = ExtractionSuggestion(
                        file=file.path,
                        function=func.name,
                        start_line=func.start_line,
                        end_line=func.end_line,
                        reason="Pure function with no UI dependencies",
                        web_ready=True,
                        estimated_effort="low",
                        dependencies=func.dependencies,
                    )
                    suggestions.append(suggestion)

            # Look for functions with minimal UI usage
            for func in file.functions:
                if not func.is_pure and len(func.ui_usage) <= 2 and func.loc >= 5:
                    suggestion = ExtractionSuggestion(
                        file=file.path,
                        function=func.name,
                        start_line=func.start_line,
                        end_line=func.end_line,
                        reason=f"Minimal UI usage: {', '.join(func.ui_usage)}",
                        web_ready=False,
                        estimated_effort="medium",
                        dependencies=func.dependencies,
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _generate_refactoring_suggestions(
        self, file_analyses: List[FileAnalysis]
    ) -> List[RefactoringSuggestion]:
        """Generate refactoring suggestions for better separation"""
        suggestions = []

        for file in file_analyses:
            if file.is_mixed_file:
                # Suggest splitting mixed files
                pure_count = sum(1 for f in file.functions if f.is_pure)
                ui_count = sum(1 for f in file.functions if len(f.ui_usage) > 0)

                if pure_count > 0 and ui_count > 0:
                    suggestion = RefactoringSuggestion(
                        file=file.path,
                        issue="Mixed UI and business logic",
                        suggestion=f"Split into separate files: {pure_count} pure functions can be moved to a logic module",
                        priority="high" if pure_count >= 3 else "medium",
                        estimated_effort="medium",
                    )
                    suggestions.append(suggestion)

            # Check for large UI classes
            for cls in file.classes:
                if cls.is_ui_class and cls.loc > 200:
                    suggestion = RefactoringSuggestion(
                        file=file.path,
                        issue=f"Large UI class: {cls.name} ({cls.loc} LOC)",
                        suggestion="Consider breaking down into smaller components or extracting business logic",
                        priority="medium",
                        estimated_effort="high",
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _generate_web_conversion_guide(
        self,
        ui_files: List[FileAnalysis],
        logic_files: List[FileAnalysis],
        mixed_files: List[FileAnalysis],
    ) -> WebConversionGuide:
        """Generate guide for converting to web application"""
        # Identify UI patterns
        ui_patterns = {}
        for file in ui_files:
            for cls in file.classes:
                if cls.is_ui_class:
                    for base in cls.bases:
                        ui_patterns[base] = ui_patterns.get(base, 0) + 1

        # Sort by frequency
        common_patterns = sorted(
            ui_patterns.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Generate recommendations
        recommendations = []

        # Recommendation 1: Reusable logic
        logic_func_count = sum(len(f.functions) for f in logic_files)
        if logic_func_count > 0:
            recommendations.append(
                f"✓ {logic_func_count} pure functions in {len(logic_files)} files are web-ready and can be reused as-is"
            )

        # Recommendation 2: UI refactoring
        if mixed_files:
            recommendations.append(
                f"⚠ {len(mixed_files)} mixed files need refactoring to separate UI from logic"
            )

        # Recommendation 3: Framework migration
        if common_patterns:
            main_framework = common_patterns[0][0]
            recommendations.append(
                f"ℹ Main UI framework: {main_framework} - consider React/Vue.js for web equivalent"
            )

        # Calculate complexity
        total_ui_classes = sum(len(f.classes) for f in ui_files)
        if total_ui_classes > 20:
            complexity = "high"
        elif total_ui_classes > 10:
            complexity = "medium"
        else:
            complexity = "low"

        return WebConversionGuide(
            summary=f"Project has {len(logic_files)} web-ready files and {len(ui_files) + len(mixed_files)} files requiring UI conversion",
            reusable_modules=[f.path for f in logic_files],
            ui_components_to_replace=[f.path for f in ui_files],
            recommended_approach="API-based separation: Use FastAPI for backend (reuse logic), React for frontend (replace UI)",
            estimated_complexity=complexity,
            recommendations=recommendations,
        )

    def _calculate_web_ready_percentage(
        self, file_analyses: List[FileAnalysis]
    ) -> float:
        """Calculate percentage of code that is web-ready"""
        if not file_analyses:
            return 0.0

        total_loc = sum(f.loc for f in file_analyses)
        if total_loc == 0:
            return 0.0

        # Logic files are 100% web-ready
        logic_loc = sum(f.loc for f in file_analyses if f.is_logic_file)

        # Mixed files: estimate based on pure functions
        mixed_loc = 0
        for f in file_analyses:
            if f.is_mixed_file:
                pure_func_loc = sum(func.loc for func in f.functions if func.is_pure)
                mixed_loc += pure_func_loc

        web_ready_loc = logic_loc + mixed_loc

        return round((web_ready_loc / total_loc) * 100, 2)
