"""Build a reproducible installable skill ZIP without development files."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile

FILES = ("SKILL.md", "LICENSE", "agents/openai.yaml", "scripts/assemble_video.py")
DIRECTORIES = ("references", "assets")


def build_release(source: Path, destination: Path, version: str) -> Path:
    source, destination = Path(source), Path(destination)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?", version):
        raise ValueError("Use a semantic version such as 1.0.0")
    paths = []
    for name in FILES:
        path = source / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing required regular file: {name}")
        paths.append(path)
    for name in DIRECTORIES:
        directory = source / name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"Missing required regular directory: {name}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlinks are not distributable: {path.relative_to(source)}")
            if path.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(directory).parts):
                paths.append(path)
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"llm-explain-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in sorted(paths, key=lambda item: item.relative_to(source).as_posix()):
            name = "llm-explain/" + path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()
    print(build_release(args.source, args.output, args.version))


if __name__ == "__main__":
    main()
