import io
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from main import app


def make_wav():
    buffer = io.BytesIO()
    sf.write(
        buffer,
        0.1 * np.sin(2 * np.pi * 200 * np.arange(16_000) / 16_000),
        16_000,
        format="WAV",
    )
    return buffer.getvalue()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_does_not_load_model(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_analysis_returns_both_class_scores(self):
        with patch("main.analyze_audio", return_value=(0.7, 0.3)):
            response = self.client.post(
                "/api/analyze",
                files={"audio": ("clip.wav", make_wav(), "audio/wav")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "verdict": "AI-generated voice likely",
                "fake_probability": 0.7,
                "real_probability": 0.3,
                "duration_seconds": 1.0,
            },
        )


if __name__ == "__main__":
    unittest.main()
