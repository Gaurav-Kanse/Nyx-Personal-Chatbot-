import sounddevice as sd
import numpy as np

class SoundDeviceAudioInterface:
    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.stream = None
        self.running = False

        # Check if input device exists
        try:
            sd.check_input_settings(
                samplerate=self.samplerate,
                channels=self.channels
            )
            self.available = True
        except Exception as e:
            print("⚠️ Mic not detected, switching to TEXT MODE")
            print(f"Reason: {e}")
            self.available = False

    def start(self, input_callback):
        if not self.available:
            raise RuntimeError("Microphone unavailable")

        self.running = True

        def callback(indata, frames, time, status):
            if status:
                print(status)

            if not self.running:
                return

            audio = (indata[:, 0] * 32767).astype(np.int16)
            input_callback(audio.tobytes())

        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def output(self, audio_bytes):
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        sd.play(audio, self.samplerate)
        sd.wait()
