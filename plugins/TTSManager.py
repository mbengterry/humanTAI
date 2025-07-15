import threading
import queue
import pyttsx3
import platform
class TTSManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init(self):
        if self._initialized:
            return
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._initialized = True

    def _run(self):
        system = platform.system()
        if system == "Windows":
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.75)
            try:
                engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
            except Exception:
                pass
        while True:
            text = self.queue.get()
            if text is None:
                break
            try:
                if system == "Windows":
                    engine.say(text)
                    engine.runAndWait()
                elif system == "Darwin":  # macOS
                    import subprocess
                    subprocess.run(["say", text])
                else:
                    print(f"TTS not supported on {system}")
            except Exception as e:
                print("TTS thread error:", e)

    def speak(self, text):
        if not self._initialized:
            self._init()
        self.queue.put(text)

    def shutdown(self):
        if self._initialized:
            self.queue.put(None)
            self.thread.join(timeout=2)
