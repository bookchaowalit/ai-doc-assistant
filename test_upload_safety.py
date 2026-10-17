"""Regression tests for bounded upload handling without a provider key."""

from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class UploadSafetyTests(unittest.TestCase):
    def test_rejects_unsupported_extension_before_writing(self) -> None:
        with patch.object(main.doc_processor, "process") as process:
            response = client.post(
                "/upload",
                files={
                    "file": (
                        "malware.exe",
                        b"not executable",
                        "application/octet-stream",
                    )
                },
            )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json()["detail"], "Unsupported document type")
        process.assert_not_called()

    def test_rejects_path_traversal_filename_before_writing(self) -> None:
        with patch.object(main.doc_processor, "process") as process:
            response = client.post(
                "/upload",
                files={"file": ("../../secrets.txt", b"not a secret", "text/plain")},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"], "Filename must be a single safe name"
        )
        process.assert_not_called()

    def test_rejects_oversized_upload_before_processing(self) -> None:
        payload = b"x" * (main.MAX_UPLOAD_BYTES + 1)
        with patch.object(main.doc_processor, "process") as process:
            response = client.post(
                "/upload",
                files={"file": ("large.txt", payload, "text/plain")},
            )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.json()["detail"], "Document exceeds the upload size limit"
        )
        process.assert_not_called()

    def test_valid_upload_uses_random_temp_file_and_cleans_it(self) -> None:
        captured_path: list[str] = []

        def fake_process(path: str, filename: str) -> dict:
            captured_path.append(path)
            self.assertTrue(Path(path).is_file())
            self.assertEqual(filename, "safe.txt")
            return {"chunks": []}

        with (
            patch.object(main.doc_processor, "process", side_effect=fake_process),
            patch.object(main.rag_engine, "ingest_chunks") as ingest,
        ):
            response = client.post(
                "/upload",
                files={"file": ("safe.txt", b"synthetic content", "text/plain")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "safe.txt")
        ingest.assert_called_once_with([])
        self.assertTrue(captured_path and not Path(captured_path[0]).exists())


if __name__ == "__main__":
    unittest.main()
