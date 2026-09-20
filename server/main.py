"""MuBoxing audio feature API. No uploaded audio is retained."""

from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 50 * 1024 * 1024
SAMPLE_RATE = 11025
HOP = 4096
ALLOWED = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"}

app = FastAPI(title="MuBoxing audio analysis")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nyk5473.github.io", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/")
def homepage():
    return FileResponse(ROOT / "index.html")


@app.get("/{filename}")
def asset(filename: str):
    if filename not in {"intex.html", "PARADISE (FEAT. FANXYCHILD)-mc.mp3"}:
        raise HTTPException(404)
    return FileResponse(ROOT / filename)


def analyze_pcm(samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> dict:
    """Measure energy, frequency balance and changes; no source separation claims."""
    if samples.size < sample_rate:
        raise ValueError("1초 이상의 오디오가 필요합니다.")
    duration = samples.size / sample_rate
    frame = 8192
    frames = np.lib.stride_tricks.sliding_window_view(samples, frame)[::HOP]
    if len(frames) == 0:
        raise ValueError("오디오가 너무 짧습니다.")
    windowed = frames * np.hanning(frame)
    spectrum = np.abs(np.fft.rfft(windowed, axis=1))
    freqs = np.fft.rfftfreq(frame, 1 / sample_rate)
    rms = np.sqrt(np.mean(windowed * windowed, axis=1))
    band_edges = [(20, 250), (250, 2000), (2000, 5500)]
    bands = np.stack([
        np.mean(spectrum[:, (freqs >= lo) & (freqs < hi)], axis=1)
        for lo, hi in band_edges
    ], axis=1)
    bands = np.log1p(bands)
    bands /= np.maximum(np.percentile(bands, 95, axis=0), 1e-9)
    bands = np.clip(bands, 0, 1)
    energy = rms / max(float(np.percentile(rms, 95)), 1e-9)
    energy = np.clip(energy, 0, 1)
    change = np.zeros(len(rms))
    change[1:] = np.maximum(0, np.diff(energy)) + np.mean(
        np.maximum(0, np.diff(bands, axis=0)), axis=1
    )

    # Fixed 8-second windows keep the timeline legible; labels describe measurements.
    sections = []
    freq_map = {}
    tracks = [
        {"name": "저역", "color": "var(--bass)", "segs": []},
        {"name": "중역", "color": "var(--chords)", "segs": []},
        {"name": "고역", "color": "var(--high)", "segs": []},
        {"name": "에너지", "color": "var(--drums)", "segs": []},
        {"name": "변화", "color": "var(--fx)", "segs": []},
    ]
    step = 8.0
    for n, start in enumerate(np.arange(0, duration, step)):
        end = min(float(start + step), duration)
        a = min(int(start * sample_rate / HOP), len(rms) - 1)
        b = max(a + 1, min(int(end * sample_rate / HOP), len(rms)))
        vals = np.mean(bands[a:b], axis=0)
        loud = float(np.mean(energy[a:b]))
        novelty = float(np.mean(change[a:b]))
        label = f"구간 {n + 1}"
        sections.append({"label": label, "start": round(float(start), 2), "end": round(end, 2)})
        freq_map[label] = [round(float(v), 3) for v in vals]
        levels = [*vals, loud, min(novelty * 4, 1)]
        for track, level in zip(tracks, levels):
            if level >= (0.12 if track["name"] == "변화" else 0.18):
                track["segs"].append({
                    "s": round(float(start), 2), "e": round(end, 2),
                    "label": f"{int(level * 100)}%",
                })
    return {
        "data": {"TOTAL": round(duration, 2), "sections": sections, "tracks": tracks},
        "harmony": {
            "top": [], "bottom": [], "freq": freq_map,
            "noteText": "실제 음원의 에너지와 저·중·고역 주파수 분포를 측정했습니다. 악기 분리, 보컬 감지, 코드 추정은 제공하지 않습니다.",
        },
        "metrics": {"duration": round(duration, 2), "peak_energy": round(float(np.max(energy)), 3)},
    }


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if Path(file.filename or "").suffix.lower() not in ALLOWED:
        raise HTTPException(400, "지원하지 않는 오디오 형식입니다.")
    chunks = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > MAX_BYTES:
            raise HTTPException(413, "파일은 50MB 이하여야 합니다.")
        chunks.append(chunk)
    if not size:
        raise HTTPException(400, "빈 파일입니다.")
    try:
        decoded = subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", "pipe:0",
             "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE),
             "-t", "600", "pipe:1"],
            input=b"".join(chunks), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=90, check=False,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(422, "오디오 변환 시간이 초과되었습니다.")
    if decoded.returncode or not decoded.stdout:
        raise HTTPException(422, "오디오를 읽을 수 없습니다.")
    samples = np.frombuffer(decoded.stdout, dtype="<i2").astype(np.float32) / 32768
    try:
        return analyze_pcm(samples)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
