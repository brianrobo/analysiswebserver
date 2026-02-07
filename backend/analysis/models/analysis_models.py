"""
Pydantic models for PyQt/PySide analysis results
"""
from typing import Optional
from pydantic import BaseModel, Field


class Import(BaseModel):
    """Import statement information"""
    module: str = Field(..., description="Module name (e.g., 'PyQt5.QtWidgets')")
    names: list[str] = Field(default_factory=list, description="Imported names")
    is_ui: bool = Field(False, description="Is this a UI framework import?")
    line_number: int = Field(..., description="Line number in source file")


class FunctionInfo(BaseModel):
    """Function definition information"""
    name: str = Field(..., description="Function name")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    loc: int = Field(..., description="Lines of code")
    is_pure: bool = Field(False, description="Is this a pure function (no UI dependencies)?")
    ui_usage: list[str] = Field(default_factory=list, description="UI calls used in function")
    dependencies: list[str] = Field(default_factory=list, description="External dependencies (numpy, pandas, etc.)")
    has_global_access: bool = Field(False, description="Accesses global variables")


class ClassInfo(BaseModel):
    """Class definition information"""
    name: str = Field(..., description="Class name")
    bases: list[str] = Field(default_factory=list, description="Base class names")
    is_ui_class: bool = Field(False, description="Inherits from UI class (QWidget, QMainWindow, etc.)")
    methods: list[FunctionInfo] = Field(default_factory=list, description="Class methods")
    loc: int = Field(..., description="Lines of code")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")


class FileAnalysis(BaseModel):
    """Analysis result for a single Python file"""
    path: str = Field(..., description="File path relative to project root")
    imports: list[Import] = Field(default_factory=list, description="Import statements")
    classes: list[ClassInfo] = Field(default_factory=list, description="Class definitions")
    functions: list[FunctionInfo] = Field(default_factory=list, description="Top-level functions")
    loc: int = Field(..., description="Total lines of code")
    is_ui_file: bool = Field(False, description="File contains UI code")
    is_logic_file: bool = Field(False, description="File contains only pure logic")
    is_mixed_file: bool = Field(False, description="File contains both UI and logic")
    ui_percentage: float = Field(0.0, ge=0, le=100, description="Percentage of UI code (0-100)")


class ExtractionSuggestion(BaseModel):
    """Suggestion for extracting pure logic from mixed code"""
    file: str = Field(..., description="File path")
    function: str = Field(..., description="Function name to extract")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    reason: str = Field(..., description="Why this should be extracted")
    web_ready: bool = Field(False, description="Ready to use in web backend without changes")
    estimated_effort: str = Field(..., description="Effort level: low, medium, high")
    dependencies: list[str] = Field(default_factory=list, description="Required dependencies")


class RefactoringSuggestion(BaseModel):
    """Suggestion for refactoring code"""
    file: str = Field(..., description="File path")
    issue: str = Field(..., description="Identified issue")
    suggestion: str = Field(..., description="Refactoring suggestion")
    priority: str = Field(..., description="Priority: low, medium, high")
    line_numbers: Optional[str] = Field(None, description="Affected line numbers (e.g., '10-25')")


class WebConversionGuide(BaseModel):
    """Guide for converting to web application"""
    summary: str = Field(..., description="Summary of conversion requirements")
    reusable_modules: list[str] = Field(default_factory=list, description="Modules that can be reused as-is")
    ui_components_to_replace: list[str] = Field(default_factory=list, description="UI components that need replacement")
    recommended_approach: str = Field(..., description="Recommended conversion approach")
    estimated_complexity: str = Field(..., description="Estimated complexity (low/medium/high)")
    recommendations: list[str] = Field(default_factory=list, description="Specific recommendations")


class ProjectAnalysisResult(BaseModel):
    """Complete analysis result for a PyQt/PySide project"""
    project_name: str = Field(..., description="Project name (from directory)")
    total_files: int = Field(..., description="Total Python files analyzed")
    analysis_summary: dict = Field(
        default_factory=lambda: {"ui_files": 0, "logic_files": 0, "mixed_files": 0},
        description="Quick summary counts"
    )
    ui_files: list[FileAnalysis] = Field(default_factory=list, description="Files with only UI code")
    logic_files: list[FileAnalysis] = Field(default_factory=list, description="Files with only logic code")
    mixed_files: list[FileAnalysis] = Field(default_factory=list, description="Files with mixed UI and logic")
    extraction_suggestions: list[ExtractionSuggestion] = Field(
        default_factory=list,
        description="Suggestions for extracting pure logic"
    )
    refactoring_suggestions: list[RefactoringSuggestion] = Field(
        default_factory=list,
        description="General refactoring suggestions"
    )
    web_conversion_guide: WebConversionGuide = Field(
        default_factory=WebConversionGuide,
        description="Guide for web conversion"
    )
