"""Release tests check the distributable, not the wording of the skill."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def load_builder(self):
        path = ROOT / "scripts/build_release.py"
        self.assertTrue(path.is_file(), "Release builder has not been implemented")
        spec = importlib.util.spec_from_file_location("build_release", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, path):
        for name, content in {
            "SKILL.md": "---\nname: llm-explain\ndescription: Use when learning.\n---\n[text](references/text.md)\n",
            "agents/openai.yaml": 'interface:\n  display_name: "LLM Explain"\n',
            "references/text.md": "Clear language.\n",
            "assets/example.html": "<!doctype html><title>Example</title>",
            "scripts/assemble_video.py": 'print("example")\n',
            "LICENSE": "Test license\n",
            "README.md": "Development README\n",
            "docs/private.md": "DO NOT DISTRIBUTE\n",
            ".env": "FAKE_SECRET=not-a-real-secret\n",
            "scripts/build_release.py": "Development tooling\n",
        }.items():
            item = path / name
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_text(content)

    def test_archive_has_one_portable_root_and_excludes_development_files(self):
        builder = self.load_builder()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.fixture(base / "source")
            archive = builder.build_release(base / "source", base / "out", "1.0.0")
            with zipfile.ZipFile(archive) as package:
                names = set(package.namelist())
                self.assertIn("llm-explain/SKILL.md", names)
                self.assertIn("llm-explain/scripts/assemble_video.py", names)
                self.assertNotIn("llm-explain/.env", names)
                self.assertFalse(any("private" in name or "build_release" in name for name in names))
                self.assertTrue(all(name.startswith("llm-explain/") for name in names))
                package.extractall(base / "unpacked")
            self.assertTrue((base / "unpacked/llm-explain/references/text.md").is_file())

    def test_identical_sources_produce_identical_bytes_and_checksum(self):
        builder = self.load_builder()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.fixture(base / "source")
            first = builder.build_release(base / "source", base / "one", "1.0.0")
            second = builder.build_release(base / "source", base / "two", "1.0.0")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            digest = hashlib.sha256(first.read_bytes()).hexdigest()
            self.assertEqual(first.with_suffix(".zip.sha256").read_text(), f"{digest}  {first.name}\n")

    def test_missing_required_file_and_symlinks_are_rejected(self):
        builder = self.load_builder()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.fixture(base / "source")
            (base / "source/SKILL.md").unlink()
            with self.assertRaises(ValueError):
                builder.build_release(base / "source", base / "out", "1.0.0")
            self.fixture(base / "source")
            (base / "source/assets/leak.txt").symlink_to(base / "source/.env")
            with self.assertRaises(ValueError):
                builder.build_release(base / "source", base / "out", "1.0.0")

    def test_unsafe_version_is_rejected(self):
        builder = self.load_builder()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.fixture(base / "source")
            with self.assertRaises(ValueError):
                builder.build_release(base / "source", base / "out", "../../escape")


if __name__ == "__main__":
    unittest.main()
