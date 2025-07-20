import multiprocessing
import platform
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'  # ✅ 禁止图形窗口（必须放在 pygame 导入前）
from gtts import gTTS
import tempfile
import subprocess

def tts_process_main(queue):
    
    def say_with_gtts(text, lang='en', speed=1.5, volume=0.3):
        # 生成 TTS MP3 文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(f.name)
            temp_path = f.name

        try:
            # 构建 ffplay 命令，静音播放窗口，设置速度和音量
            cmd = [
                'ffplay',
                '-nodisp',              # 不显示视频窗口
                '-autoexit',            # 播放完退出
                '-loglevel', 'quiet',   # 静音日志输出
                '-af', f'atempo={speed},volume={volume}',
                temp_path
            ]
            subprocess.run(cmd)
        finally:
            os.remove(temp_path)  # 删除临时文件

    system = platform.system()

    if system == 'Darwin':
        # macOS: use pyttsx3
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.5)
        while True:
            text = queue.get()
            if text is None:
                break
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print("TTS (macOS) error:", e)

    else:
        # Linux (WSL): use gTTS + ffplay
        while True:
            text = queue.get()
            if text is None:
                break
            try:
                say_with_gtts(text, lang='en', speed=2, volume=0.1)
            except Exception as e:
                print("TTS (Linux) error:", e)


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