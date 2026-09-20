import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np
from fastapi import HTTPException

from server.main import SAMPLE_RATE, analyze_video


class VideoAnalysisTests(unittest.TestCase):
    def test_rejects_invalid_video_id(self):
        with self.assertRaises(HTTPException) as error:
            analyze_video("https://not-youtube.example/private")
        self.assertEqual(error.exception.status_code, 400)

    def test_video_audio_is_measured_and_temp_file_removed(self):
        downloaded = []

        class FakeDownloader:
            def __init__(self, options):
                self.path = Path(options["outtmpl"].replace("%(ext)s", "wav"))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def extract_info(self, url, download):
                self.assert_url = url
                samples = (np.sin(2 * np.pi * 440 * np.arange(SAMPLE_RATE * 3) / SAMPLE_RATE) * 12000).astype("<i2")
                with wave.open(str(self.path), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(SAMPLE_RATE)
                    wav.writeframes(samples.tobytes())
                downloaded.append(self.path)
                return {"title": "Test tone", "uploader": "Test", "duration": 3}

            def prepare_filename(self, info):
                return str(self.path)

        with patch("server.main.yt_dlp.YoutubeDL", FakeDownloader):
            result = analyze_video("M7lc1UVf-VE")
        self.assertEqual(result["data"]["TOTAL"], 3)
        self.assertEqual(result["video"]["title"], "Test tone")
        self.assertEqual(len(result["data"]["tracks"]), 5)
        self.assertFalse(downloaded[0].exists())


if __name__ == "__main__":
    unittest.main()
