# 文件路径：core/widgets/popup.py

import pyglet
from core.constants import COLORS as C

class PopUp:
    def __init__(self, name, title='提示', text='', width=300, height=100, font_size=14, color=(255, 0, 0, 255)):
        self.window = pyglet.window.Window(width=width, height=height, caption=title, visible=False)
        self.label = pyglet.text.Label(
            text,
            font_size=font_size,
            x=width // 2, y=height // 2,
            anchor_x='center', anchor_y='center',
            color=color  # ← 使用传入颜色
        )
        self.text = text
        self.visible = False

        @self.window.event
        def on_draw():
            self.window.clear()
            self.label.draw()


    def show(self, text=''):
        self.label.text = text
        self.window.set_visible(True)
        self.visible = True

    def hide(self):
        self.window.set_visible(False)
        self.visible = False
