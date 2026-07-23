"""
voice.py — STT (Whisper) + TTS (Edge TTS ou Kokoro) pour Nadia Desktop.

Whisper écoute le micro → texte → handle_instruction → TTS parle.
"""

from __future__ import annotations

import asyncio
import io
import logging
import queue
import threading
from typing import Callable

from core.tts_text import prepare_text_for_speech, split_for_speech

logger = logging.getLogger(__name__)

# ── STT — Whisper ────────────────────────────────────────────────────────────


class SpeechListener:
    """
    Écoute le micro en continu et appelle on_text(texte) quand
    une phrase est détectée.
    Utilise faster-whisper pour la vitesse sur CPU/GPU.
    """

    def __init__(
        self,
        on_text: Callable[[str], None],
        model_size: str = "base",
        language: str = "fr",
        wake_word: str | None = None,
    ) -> None:
        self.on_text = on_text
        self.language = language
        self.wake_word = wake_word.lower() if wake_word else None
        self._q: queue.Queue[bytes] = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None

        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(model_size, device="auto", compute_type="int8")
            logger.info("Whisper %s chargé", model_size)
        except ImportError:
            logger.warning("faster-whisper non installé — STT désactivé")
            self._model = None

    def start(self) -> None:
        if self._model is None:
            logger.warning("Whisper non disponible — STT inactif")
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _listen_loop(self) -> None:
        try:
            import numpy as np
            import sounddevice as sd

            sample_rate = 16_000
            chunk = 1024
            silence_db = -40
            silence_sec = 1.2
            min_speech = 0.4

            buffer: list[np.ndarray] = []
            silent_frames = 0
            speaking = False
            frames_per_sec = sample_rate // chunk

            def callback(indata, frames, time, status):
                self._q.put(indata.copy())

            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk,
                callback=callback,
            ):
                logger.info("Micro actif")
                while self._running:
                    try:
                        chunk_data = self._q.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    rms_db = 20 * np.log10(np.sqrt(np.mean(chunk_data**2)) + 1e-10)

                    if rms_db > silence_db:
                        speaking = True
                        silent_frames = 0
                        buffer.append(chunk_data)
                    elif speaking:
                        silent_frames += 1
                        buffer.append(chunk_data)
                        if silent_frames >= int(silence_sec * frames_per_sec):
                            duration = len(buffer) * chunk / sample_rate
                            if duration >= min_speech:
                                audio = np.concatenate(buffer).flatten()
                                self._transcribe(audio, sample_rate)
                            buffer = []
                            speaking = False
                            silent_frames = 0

        except Exception as e:
            logger.error("STT loop error : %s", e)

    def _transcribe(self, audio, sample_rate: int) -> None:
        if self._model is None:
            return
        try:
            segments, _ = self._model.transcribe(
                audio,
                language=self.language,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(s.text for s in segments).strip()
            if not text:
                return

            if self.wake_word:
                lower = text.lower()
                if self.wake_word in lower:
                    text = lower.split(self.wake_word, 1)[-1].strip()
                else:
                    return

            logger.debug("STT → %s", text)
            if text:
                self.on_text(text)
        except Exception as e:
            logger.error("Transcription error : %s", e)


# ── TTS — Edge TTS (défaut) + Kokoro (optionnel) ────────────────────────────


class Speaker:
    """Synthèse vocale — Edge TTS (Microsoft, gratuit) ou Kokoro local."""

    def __init__(
        self,
        backend: str = "edge",
        voice: str = "fr-FR-VivienneMultilingualNeural",
        rate: str = "-8%",
        pitch: str = "+2Hz",
    ) -> None:
        self.backend = backend
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._generation = 0

    def stop(self) -> None:
        """Stop current playback (e.g. new user message)."""
        self._cancel.set()
        self._generation += 1
        try:
            import sounddevice as sd

            sd.stop()
        except Exception:
            pass

    def speak(self, text: str) -> None:
        """Synthétise et joue le texte (non bloquant)."""
        spoken = prepare_text_for_speech(text)
        if not spoken:
            logger.debug("TTS skipped — nothing speakable after cleanup")
            return

        self.stop()
        self._cancel.clear()
        generation = self._generation

        t = threading.Thread(
            target=self._speak_sync,
            args=(spoken, generation),
            daemon=True,
        )
        t.start()

    def _speak_sync(self, text: str, generation: int) -> None:
        with self._lock:
            if self._cancel.is_set() or generation != self._generation:
                return
            if self.backend == "kokoro":
                self._kokoro_tts(text, generation)
            else:
                self._edge_tts(text, generation)

    def _edge_tts(self, text: str, generation: int) -> None:
        try:
            import edge_tts
            import sounddevice as sd
            import soundfile as sf

            chunks = split_for_speech(text)
            if not chunks:
                return

            async def _synthesize(sentence: str) -> bytes:
                communicate = edge_tts.Communicate(
                    sentence,
                    self.voice,
                    rate=self.rate,
                    pitch=self.pitch,
                )
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                return audio_data

            for i, sentence in enumerate(chunks):
                if self._cancel.is_set() or generation != self._generation:
                    return

                audio_bytes = asyncio.run(_synthesize(sentence))
                if not audio_bytes:
                    continue

                buf = io.BytesIO(audio_bytes)
                data, samplerate = sf.read(buf)

                if self._cancel.is_set() or generation != self._generation:
                    return

                sd.play(data, samplerate)
                sd.wait()

                # Short pause between sentences — more natural than one long block.
                if i < len(chunks) - 1:
                    if self._cancel.is_set() or generation != self._generation:
                        return
                    sd.sleep(int(280 + min(len(sentence), 120) * 2))

        except ImportError:
            logger.warning("edge-tts non installé — parole muette")
        except Exception as e:
            logger.error("Edge TTS error : %s", e)

    def _kokoro_tts(self, text: str, generation: int) -> None:
        try:
            import sounddevice as sd
            from kokoro_onnx import Kokoro

            if self._cancel.is_set() or generation != self._generation:
                return

            kokoro = Kokoro("kokoro-v1_0.onnx", "voices-v1_0.bin")
            samples, sample_rate = kokoro.create(
                text,
                voice="af_bella",
                speed=0.95,
                lang="fr-fr",
            )
            if self._cancel.is_set() or generation != self._generation:
                return
            sd.play(samples, sample_rate)
            sd.wait()
        except ImportError:
            logger.warning("kokoro-onnx non installé — fallback Edge TTS")
            self._edge_tts(text, generation)
        except Exception as e:
            logger.error("Kokoro TTS error : %s", e)
