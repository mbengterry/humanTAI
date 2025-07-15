# Copyright 2023, by Julien Cegarra & Benoît Valéry. All rights reserved.
# Institut National Universitaire Champollion (Albi, France).
# License : CeCILL, version 2.1 (see the LICENSE file)

from core.widgets.abstractwidget import *
from core.constants import FONT_SIZES as F
from core.constants import COLORS as C
from pyglet import shapes

class Simpletext(AbstractWidget):
    def __init__(self, name, container, text, draw_order=1, font_size=F['SMALL'],
                 x=0.5, y=0.5, wrap_width=1, color=C['BLACK'], bold=False, bgcolor=None):
        super().__init__(name, container)

        self.group = G(draw_order - 1)
        self.batch = getattr(container, 'batch', None)
        x_px = container.l + x * container.w
        y_px = container.b + y * container.h
        wrap_width_px = container.w * wrap_width
        
        from core.window import Window
        self.batch = Window.MainWindow.batch
        self.group = G(draw_order)

        if bgcolor is not None:
            self.bg = shapes.Rectangle(
                x_px, y_px, 0, 0,  # 初始为零，后续动态调整
                color=bgcolor[:3],
                batch=self.batch,
                group=G(draw_order - 1)
            )
            self.bg.opacity = 0  # 初始隐藏
        else:
            self.bg = None


        self.vertex['text'] = Label(text, font_size=font_size, x=x_px, y=y_px,
                                    align='center', anchor_x='center', anchor_y='center',
                                    color=color, bold=bold, width=wrap_width_px,
                                    multiline=True, group=G(draw_order),
                                    font_name=self.font_name, batch=self.batch)



    def set_text(self, text):
        self.vertex['text'].text = text
        if self.bg:
            if text.strip():
                label = self.vertex['text']
                width = label.content_width + 10   # 添加少许边距
                height = label.content_height + 6
                self.bg.width = width
                self.bg.height = height
                self.bg.x = label.x - width / 2
                self.bg.y = label.y - height / 2
                self.bg.opacity = 200
            else:
                self.bg.opacity = 0



    def get_text(self):
        return self.vertex['text'].text

    def set_color(self, color):
        self.vertex['text'].color = color

    def set_bold(self, bold=True):
        self.vertex['text'].bold = bold

    def set_bgcolor(self, bgcolor):
        if self.bg:
            self.bg.color = bgcolor[:3]