# Copyright 2023, by Julien Cegarra & Benoît Valéry. All rights reserved.
# Institut National Universitaire Champollion (Albi, France).
# License : CeCILL, version 2.1 (see the LICENSE file)

from core.widgets.abstractwidget import *
from core.window import Window

class Radio(AbstractWidget):
    def __init__(self, name, container, label, frequency, on):
        super().__init__(name, container)

        self.arrows = dict(arrow_up=   dict(x_ratio=-0.23, angle=0),
                           arrow_down= dict(x_ratio=-0.2, angle=math.pi),
                           arrow_left= dict(x_ratio=0.2, angle=math.pi/2),
                           arrow_right=dict(x_ratio=0.23, angle=3*math.pi/2))
        self.frequency = frequency
        self.label = label
        self.is_selected = on

        # Radio label #
        self.vertex['radio_frequency'] = Label(self.get_frequency_string(frequency), font_size=F['SMALL'],
                                               x=self.container.cx, y=self.container.cy, font_name=self.font_name,
                                               anchor_x='center', anchor_y='center',
                                               color=C['BLACK'], batch=Window.MainWindow.batch, group=G(self.m_draw+1))

        # Arrows vertices #
        # Only a change in vertices is needed to show/hide arrows --> (0, 0, 0...) = hide
        for name, info in self.arrows.items():
            self.add_vertex(name, 3, GL_TRIANGLES, G(self.m_draw+2),
                            ('v2f/dynamic', (0, 0, 0, 0, 0, 0)),
                            ('c4B/static', (C['BLACK']*3)))


        # Feedback vertices #
        # A frame slightly smaller than the radio container
        vertices = self.vertice_line_border(container.get_reduced(0.6,0.9))
        self.add_vertex('feedback_lines', 8, GL_LINES, G(self.m_draw+3),
                        ('v2f/dynamic', vertices),
                        ('c4B/dynamic', (C['BACKGROUND'] * 8)))  # Background color = invisible
        self.show()

    def show(self):
        super().show()
        if self.is_selected:
            self.show_arrows()


    def get_frequency_string(self, frequency):
        return (f"{self.label.replace('_', ' ')}\t\t\t\t\t\t\t{round(frequency, 1)}")


    def get_position(self):
        return self.pos


    def hide_arrows(self):
        for name, info in self.arrows.items():
            v = (0, 0)*3  # Get an invisible vertice (hide)
            self.on_batch[name].vertices = v
        self.is_selected = False
        self.logger.record_state(self.name, 'selected', False)


    def show_arrows(self):
        for name, info in self.arrows.items():
            v = self.get_triangle_vertice(x_ratio=info['x_ratio'], angle=info['angle'])
            self.on_batch[name].vertices = v
        self.is_selected = True
        self.logger.record_state(self.name, 'selected', True)


    def is_new_frequency(self, frequency):
        return self.get_frequency_string(frequency) != self.vertex['radio_frequency'].text


    def set_frequency_text(self, frequency):
        if not self.is_new_frequency(frequency):
            return
        self.vertex['radio_frequency'].text = self.get_frequency_string(frequency)
        self.logger.record_state(self.name, 'radio_frequency', frequency)


    def set_feedback_color(self, color):
        if color == self.get_vertex_color('feedback_lines'):
            return
        self.on_batch['feedback_lines'].colors[:] = color * 8
        self.logger.record_state(self.name, 'feedback_color', color)

    def set_highlight(self, state: bool):
        """Set the background color to highlight the radio"""
        if state:
            self.set_background_color((255, 255, 0))  # 黄色高亮
        else:
            self.set_background_color((30, 30, 30))   # 默认背景色（你可根据实际样式调整）

    def set_background_color(self, color):
        self.background_color = color
        self.need_redraw = True  # 或类似逻辑，确保界面刷新
