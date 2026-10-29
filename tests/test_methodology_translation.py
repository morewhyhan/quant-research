"""Mechanical checks for the optional translated source, not semantic proof."""
from collections import Counter
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "learning/sources/crypto-quant-research"


class MethodologyTranslationTests(unittest.TestCase):
    def test_original_and_license_match_upstream_blobs(self):
        expected = {
            "METHODOLOGY.md": "a195c62ecf6a53fe160f39082c54c698273ce8b2",
            "LICENSE": "999c983df0fe406f0c791f7cfc52679e863b8da6",
        }
        for name, blob in expected.items():
            value = (SOURCE / name).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()
            self.assertEqual(actual, blob, name)

    def test_translation_keeps_structure_numbers_and_code_paths(self):
        original = (SOURCE / "METHODOLOGY.md").read_text(encoding="utf-8")
        translation = (ROOT / "learning/strategy-validation.md").read_text(encoding="utf-8")
        body = translation[translation.index("# 方法论"): ]
        self.assertEqual(len(re.findall(r"^## ", original, re.M)), len(re.findall(r"^## ", body, re.M)))
        self.assertEqual(len(re.findall(r"^\|", original, re.M)), len(re.findall(r"^\|", body, re.M)))
        self.assertEqual(Counter(re.findall(r"\d+(?:\.\d+)?", original)),
                         Counter(re.findall(r"\d+(?:\.\d+)?", body)))
        self.assertEqual(re.findall(r"`([^`]+)`", original), re.findall(r"`([^`]+)`", body))


if __name__ == "__main__":
    unittest.main()
