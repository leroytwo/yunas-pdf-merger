"""
organize_pdfs.py

Drop this file into a folder full of .zip files (each containing PDFs),
double-click it (or the .exe built from it), and it will:

  1. Unzip each .zip into a numbered folder (1, 2, 3, ...) and delete the zip.
  2. For each folder, look at the first PDF (alphabetically), find a line on
     its first page like "YL group: SomeName", and use "SomeName" as the
     output filename.
  3. Merge all PDFs in that folder into "SomeName.pdf" in the main folder.
  4. Delete the now-empty numbered folder.

No external programs (unzip, pdftotext, pdftk) are required - everything
here is pure Python.
"""

import sys
import shutil
import zipfile
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Missing dependency 'pypdf'. If you're running this as a .py file,")
    print("install it with:  pip install pypdf")
    input("Press Enter to exit...")
    sys.exit(1)


def get_base_dir() -> Path:
    """Folder the script/exe lives in (so it works when double-clicked)."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-built .exe
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def unzip_all(base: Path) -> None:
    zip_files = sorted(base.glob("*.zip"))
    counter = 1
    for zip_path in zip_files:
        target_dir = base / str(counter)
        target_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(target_dir)
            zip_path.unlink()
            print(f"Unzipped {zip_path.name} -> {target_dir.name}/")
        except Exception as e:
            print(f"!! Failed to unzip {zip_path.name}: {e}")
        counter += 1


def extract_group_name(first_pdf: Path) -> str | None:
    try:
        reader = PdfReader(str(first_pdf))
        text = reader.pages[0].extract_text() or ""
    except Exception as e:
        print(f"!! Couldn't read {first_pdf.name}: {e}")
        return None

    for line in text.splitlines():
        if "YL group:" in line:
            return line.split("YL group:", 1)[1].strip()
    return None


def merge_folder(folder: Path, base: Path) -> None:
    pdfs = sorted(folder.glob("*.pdf"))
    if not pdfs:
        print(f"!! No PDFs found in {folder.name}, skipping.")
        return

    group_name = extract_group_name(pdfs[0])
    if not group_name:
        print(f"!! Couldn't find 'YL group:' line in {pdfs[0].name}; "
              f"using folder name '{folder.name}' instead.")
        group_name = folder.name

    # Strip characters Windows won't allow in filenames
    safe_name = "".join(c for c in group_name if c not in '<>:"/\\|?*').strip()
    output_path = base / f"{safe_name}.pdf"

    writer = PdfWriter()
    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Created {output_path.name} from {len(pdfs)} PDF(s)")

    shutil.rmtree(folder)


def main():
    base = get_base_dir()
    print(f"Working in: {base}\n")

    unzip_all(base)

    # Only process folders that are all-digit names (the ones we just made),
    # so we don't accidentally touch unrelated folders sitting nearby.
    folders = sorted(
        [p for p in base.iterdir() if p.is_dir() and p.name.isdigit()],
        key=lambda p: int(p.name),
    )

    for folder in folders:
        merge_folder(folder, base)

    print("\nAll done!")
    input("Press Enter to close this window...")


if __name__ == "__main__":
    main()
