"""
Test script for Phase 2 Analysis Engine
Tests the PyQt analysis engine on sample project
"""
import asyncio
import json
from pathlib import Path
from analysis import AnalysisEngine


async def main():
    """Run analysis engine test"""
    print("=" * 60)
    print("Phase 2: PyQt Analysis Engine Test")
    print("=" * 60)

    # Initialize engine
    engine = AnalysisEngine()

    # Sample project path
    sample_project = Path("tests/fixtures/sample_pyqt_project")

    if not sample_project.exists():
        print(f"[X] Sample project not found: {sample_project}")
        return

    print(f"\n[*] Analyzing project: {sample_project}")
    print(f"   Path: {sample_project.absolute()}\n")

    try:
        # Run analysis
        result = await engine.analyze_project(
            str(sample_project),
            project_name="Sample PyQt Tool"
        )

        # Print results
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)

        summary = result.analysis_summary
        print(f"Project Name: {result.project_name}")
        print(f"Total Files: {result.total_files}")
        print(f"Total Lines of Code: {summary['total_loc']}")
        print(f"UI Frameworks: {', '.join(summary['ui_frameworks'])}")
        print(f"\nFile Classification:")
        print(f"  - UI Files: {summary['ui_files_count']}")
        print(f"  - Logic Files: {summary['logic_files_count']}")
        print(f"  - Mixed Files: {summary['mixed_files_count']}")
        print(f"\nCode Elements:")
        print(f"  - Classes: {summary['total_classes']}")
        print(f"  - Functions: {summary['total_functions']}")
        print(f"\nWeb Readiness: {summary['web_ready_percentage']}%")

        # UI Files
        if result.ui_files:
            print("\n" + "=" * 60)
            print("UI FILES (Predominantly UI Code)")
            print("=" * 60)
            for file in result.ui_files:
                print(f"\n[FILE] {file.path}")
                print(f"   LOC: {file.loc}")
                print(f"   UI %: {file.ui_percentage:.1f}%")
                print(f"   Classes: {len(file.classes)}")
                for cls in file.classes:
                    if cls.is_ui_class:
                        print(f"     - {cls.name} (UI class, {cls.loc} LOC)")
                print(f"   Functions: {len(file.functions)}")

        # Logic Files
        if result.logic_files:
            print("\n" + "=" * 60)
            print("LOGIC FILES (Pure Business Logic)")
            print("=" * 60)
            for file in result.logic_files:
                print(f"\n[FILE] {file.path}")
                print(f"   LOC: {file.loc}")
                print(f"   Functions: {len(file.functions)}")
                pure_funcs = [f for f in file.functions if f.is_pure]
                print(f"   Pure Functions: {len(pure_funcs)}")
                for func in pure_funcs:
                    print(f"     - {func.name}() [{func.start_line}-{func.end_line}]")

        # Mixed Files
        if result.mixed_files:
            print("\n" + "=" * 60)
            print("MIXED FILES (UI + Logic Combined)")
            print("=" * 60)
            for file in result.mixed_files:
                print(f"\n[FILE] {file.path}")
                print(f"   LOC: {file.loc}")
                print(f"   UI %: {file.ui_percentage:.1f}%")
                pure_funcs = [f for f in file.functions if f.is_pure]
                ui_funcs = [f for f in file.functions if len(f.ui_usage) > 0]
                print(f"   Pure Functions: {len(pure_funcs)}")
                print(f"   UI-Dependent Functions: {len(ui_funcs)}")

        # Extraction Suggestions
        if result.extraction_suggestions:
            print("\n" + "=" * 60)
            print("EXTRACTION SUGGESTIONS")
            print("=" * 60)
            for i, sugg in enumerate(result.extraction_suggestions, 1):
                print(f"\n{i}. {sugg.function}() in {sugg.file}")
                print(f"   Lines: {sugg.start_line}-{sugg.end_line}")
                print(f"   Reason: {sugg.reason}")
                print(f"   Web Ready: {'[YES]' if sugg.web_ready else '[NO]'}")
                print(f"   Effort: {sugg.estimated_effort}")
                if sugg.dependencies:
                    print(f"   Dependencies: {', '.join(sugg.dependencies[:3])}")

        # Refactoring Suggestions
        if result.refactoring_suggestions:
            print("\n" + "=" * 60)
            print("REFACTORING SUGGESTIONS")
            print("=" * 60)
            for i, sugg in enumerate(result.refactoring_suggestions, 1):
                print(f"\n{i}. {sugg.file}")
                print(f"   Issue: {sugg.issue}")
                print(f"   Suggestion: {sugg.suggestion}")
                print(f"   Priority: {sugg.priority}")
                print(f"   Effort: {sugg.estimated_effort}")

        # Web Conversion Guide
        print("\n" + "=" * 60)
        print("WEB CONVERSION GUIDE")
        print("=" * 60)
        guide = result.web_conversion_guide
        print(f"\nSummary: {guide.summary}")
        print(f"Recommended Approach: {guide.recommended_approach}")
        print(f"Estimated Complexity: {guide.estimated_complexity}")
        print(f"\nReusable Modules ({len(guide.reusable_modules)}):")
        for module in guide.reusable_modules:
            print(f"  [OK] {module}")
        print(f"\nUI Components to Replace ({len(guide.ui_components_to_replace)}):")
        for component in guide.ui_components_to_replace:
            print(f"  [->] {component}")
        print(f"\nRecommendations:")
        for rec in guide.recommendations:
            print(f"  * {rec}")

        # Save to JSON
        output_file = "analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"\n[SAVED] Full results saved to: {output_file}")

        print("\n" + "=" * 60)
        print("[SUCCESS] ANALYSIS COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
