import sys
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.project_writer import export_completed_project


def main():
    print("=" * 60, flush=True)
    print("DevTeam AI: Exporting Project from CrewAI Storage Database", flush=True)
    print("=" * 60, flush=True)

    try:
        result = export_completed_project(
            project_name="simple_shopping_platform",
            overwrite=True,
        )

        project_dir = result["project_dir"]
        source_count = result["source_file_count"]
        report_count = result["report_file_count"]
        zip_path = result["zip_path"]
        zip_size = result["zip_size_bytes"]

        print(f"\nSUCCESS: Project exported successfully!", flush=True)
        print(f"Project Directory : {project_dir}", flush=True)
        print(f"Source Files      : {source_count} files written", flush=True)
        print(f"Reports Generated : {report_count} report copies written", flush=True)
        print(f"ZIP Archive       : {zip_path}", flush=True)
        print(f"ZIP Archive Size  : {zip_size:,} bytes", flush=True)

        print("\nExtracted Source Files:", flush=True)
        for f in result["source_files"]:
            print(f"  - {f}", flush=True)

        print("\nExtracted Reports:", flush=True)
        for r in result["report_files"]:
            print(f"  - {r}", flush=True)

        print("\n" + "=" * 60, flush=True)
        return 0

    except Exception as exc:
        print(f"\nERROR: Project export failed: {exc}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

