
import multiprocessing
import pyttsx3


def tts_process_main(queue):
    engine = pyttsx3.init()
    engine.setProperty('rate', 180)
    engine.setProperty('volume', 0.75)
    while True:
        text = queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("TTS process error:", e)


class TTSProcessManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init(self):
        if getattr(self, '_initialized', False):
            return
        # On Windows, multiprocessing requires the 'spawn' method and all process creation must be under __main__
        import sys
        if sys.platform == 'win32':
            multiprocessing.set_start_method('spawn', force=True)
        from .tts_manager import tts_process_main  # Ensure correct import for multiprocessing
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=tts_process_main, args=(self.queue,), daemon=True)
        self.process.start()
        self._initialized = True

    def speak(self, text):
        if not getattr(self, '_initialized', False):
            self._init()
        self.queue.put(text)

    def shutdown(self):
        if getattr(self, '_initialized', False):
            self.queue.put(None)
            self.process.join(timeout=2)
