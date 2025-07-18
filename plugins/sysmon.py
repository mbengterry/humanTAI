# Copyright 2023-2024, by Julien Cegarra & Benoît Valéry. All rights reserved.
# Institut National Universitaire Champollion (Albi, France).
# License : CeCILL, version 2.1 (see the LICENSE file)
import pyglet
from core.pseudorandom import choice, sample
from core.container import Container
from core.constants import COLORS as C
from core.widgets import Scale, Light,Simpletext
from plugins.abstractplugin import AbstractPlugin
from core import validation
from pyglet.media import Player
import pyglet
from core.widgets.popup import PopUp
from core.constants import FONTSIZE as F

from plugins.tts_manager import TTSProcessManager
from plugins.TTSManager import TTSManager




# Use this singleton, but do NOT instantiate at import time
tts_manager = TTSManager()

class Sysmon(AbstractPlugin):
    def __init__(self, label='', taskplacement='topleft', taskupdatetime=200):
        super().__init__('System monitoring', taskplacement, taskupdatetime)

        self.validation_dict = {
            'alerttimeout': validation.is_positive_integer,
            'automaticsolverdelay': validation.is_positive_integer,
            'allowanykey': validation.is_boolean,
            'lights-1-name': validation.is_string,
            'lights-1-failure': validation.is_boolean,
            'lights-1-on': validation.is_boolean,
            'lights-1-default': (validation.is_in_list, ['on', 'off']),
            'lights-1-oncolor': validation.is_color,
            'lights-1-key': validation.is_key,
            'lights-1-onfailure': validation.is_boolean,
            'lights-2-name': validation.is_string,
            'lights-2-failure': validation.is_boolean,
            'lights-2-on': validation.is_boolean,
            'lights-2-default': (validation.is_in_list, ['on', 'off']),
            'lights-2-oncolor': validation.is_color,
            'lights-2-key': validation.is_key,
            'lights-2-onfailure': validation.is_boolean,
            'scales-1-name': validation.is_string,
            'scales-1-failure': validation.is_boolean,
            'scales-1-side': (validation.is_in_list, ['-1', '0', '1']),
            'scales-1-key': validation.is_key,
            'scales-1-onfailure': validation.is_boolean,
            'scales-2-name': validation.is_string,
            'scales-2-failure': validation.is_boolean,
            'scales-2-side': (validation.is_in_list, ['-1', '0', '1']),
            'scales-2-key': validation.is_key,
            'scales-2-onfailure': validation.is_boolean,
            'scales-3-name': validation.is_string,
            'scales-3-failure': validation.is_boolean,
            'scales-3-side': (validation.is_in_list, ['-1', '0', '1']),
            'scales-3-key': validation.is_key,
            'scales-3-onfailure': validation.is_boolean,
            'scales-4-name': validation.is_string,
            'scales-4-failure': validation.is_boolean,
            'scales-4-side': (validation.is_in_list, ['-1', '0', '1']),
            'scales-4-key': validation.is_key,
            'scales-4-onfailure': validation.is_boolean}


        self.keys = {'F1', 'F2', 'F3', 'F4', 'F5', 'F6'}
        self.moving_seed = 1                # Useful for pseudorandom generation of
                                            # multiple values at once (arrows move)

        new_par = dict(alerttimeout=10000, automaticsolver=False, automaticsolverdelay=1000,
                       displayautomationstate=True, allowanykey=False, feedbackduration=1500,

                       feedbacks=dict(positive=dict(active=True, color=C['GREEN']),
                                      negative=dict(active=True, color=C['RED'])),

                       lights=dict([('1', dict(name='F5', failure=False, default='on',
                                     oncolor=C['GREEN'], key='F5', on=True)),
                                    ('2', dict(name='F6', failure=False, default='off',
                                     oncolor=C['RED'], key='F6', on=False))]),

                       scales=dict([('1', dict(name='F1', failure=False, side=0, key='F1')),
                                    ('2', dict(name='F2', failure=False, side=0, key='F2')),
                                    ('3', dict(name='F3', failure=False, side=0, key='F3')),
                                    ('4', dict(name='F4', failure=False, side=0, key='F4'))])
                       )

        self.parameters.update(new_par)

        # Add private parameters
        # to any gauge
        for gauge in self.get_all_gauges():
            gauge.update({'_failuretimer':None, '_onfailure':False, '_milliresponsetime':0,
                          '_freezetimer':None})

        # and to scale only
        for gauge in self.get_scale_gauges():
            gauge.update({'_pos':5, '_zone':0, '_feedbacktimer':None, '_feedbacktype':None})

        self.automode_position = (0.5, 0.05)
        self.scale_zones = {1: list(range(3)), 0: list(range(3, 8)), -1: list(range(8, 11))}


    def get_response_timers(self):
        return [g['_milliresponsetime'] for g in self.get_all_gauges()]


    def create_widgets(self):
        super().create_widgets()
        # Widgets coordinates (the left l coordinate is variable)
        scale_w = self.task_container.w * 0.1
        scale_b = self.task_container.b + self.task_container.h * 0.15
        scale_h = self.task_container.h * 0.5

        light_w = self.task_container.w * 0.4
        light_b = self.task_container.b + self.task_container.h * 0.75
        light_h = self.task_container.h * 0.15

        for scale_n, scale in self.parameters['scales'].items():
            scale_l = self.task_container.l + (self.task_container.w / 4) * (int(scale_n) - 1) + \
                      self.task_container.w/8 - scale_w/2
            scale_container = Container(f'scale_{scale_n}', scale_l, scale_b, scale_w, scale_h)

            scale['widget'] = self.add_widget(f"scale{str(scale_n)}", Scale,
                                             container=scale_container,
                                             label=scale['name'],
                                             arrow_position=scale['_pos'])

        for light_n, light in self.parameters['lights'].items():
            light_l = self.task_container.l + (self.task_container.w/2) * (int(light_n)-1) + \
                      self.task_container.w/4 - light_w/2
            light_container = Container(f'light_{light_n}', light_l, light_b, light_w, light_h)

            light['widget'] = self.add_widget(f'light{str(light_n)}', Light,
                                             container=light_container,
                                             label=light['name'],
                                             color=self.determine_light_color(light))

        self.add_widget(
            'alert',
            Simpletext,
            container=self.task_container,
            text='',
            color=(255, 255, 0, 255),     # 黄色文字
            bgcolor=(255, 0, 0, 255),     # 红色背景
            draw_order=5,
            x=0.5,
            y=0.025    # 靠近底部    
        )

    def compute_next_plugin_state(self):
        if not super().compute_next_plugin_state():
            return

        # For the gauges that are on failure
        for gauge in self.get_gauges_on_failure():
            # Decrement their failure timer / increment their response time
            gauge['_failuretimer'] -= self.parameters['taskupdatetime']
            gauge['_milliresponsetime'] += self.parameters['taskupdatetime']

            # If the failure timer has ended by itself, stop failure and trigger a negative feedback
            # if possible (scale gauges)
            if gauge['_failuretimer'] <= 0:
                self.stop_failure(gauge, success=False)

        for gauge in self.get_scale_gauges():
            if gauge['_feedbacktimer'] is not None:
                gauge['_feedbacktimer'] -= self.parameters['taskupdatetime']
                if gauge['_feedbacktimer'] <= 0:
                    gauge['_feedbacktimer'] = None
                    gauge['_feedbacktype'] = None


        # Compute arrows next position
        for scale_n, scale in self.parameters['scales'].items():
            self.moving_seed += 1
            # Manage the case where the arrow must change its zone
            if scale['_pos'] not in self.scale_zones[scale['_zone']]:
                scale['_pos'] = sample(self.scale_zones[scale['_zone']], self.alias,
                                       self.scenario_time, self.moving_seed)
            else:   # Move into a delimited zone
                direction = sample([-1, 1], self.alias, self.scenario_time, self.moving_seed)
                if scale['_pos'] + direction in self.scale_zones[scale['_zone']]:
                    scale['_pos'] += direction
                else:
                    scale['_pos'] -= direction

            # If the gauge freeze timer is not null, freeze its arrow (pos = )
            if scale['_freezetimer'] is not None and isinstance(scale['_freezetimer'], int):
                scale['_freezetimer'] -= self.parameters['taskupdatetime']
                if scale['_freezetimer'] > 0:
                    # Here, freeze position
                    scale['_pos'] = 5  # TODO: Check central scale value
                else:
                    scale['_freezetimer'] = None


        # Check for failure
        for gauge in self.get_gauges_key_value('failure', True):
            self.start_failure(gauge)


    def refresh_widgets(self):
        if not super().refresh_widgets():
            return
        for scale_n, scale in self.parameters['scales'].items():
            scale['widget'].set_arrow_position(scale['_pos'])

            if scale['_feedbacktimer'] is not None:
                color = self.parameters['feedbacks'][scale['_feedbacktype']]['color']
                scale['widget'].set_feedback_color(color)
                scale['widget'].set_feedback_visibility(True)

            # Feedback timer is over and the feedback is yet visible
            # Hide the feedback
            else:
                scale['widget'].set_feedback_visibility(False)
             # 🆕 文字状态显示
            label_text = f"{scale['name']}  {'abnormal' if scale['_onfailure'] else 'normal'}"
            scale['widget'].set_label(label_text)

        for light_n, light in self.parameters['lights'].items():
            light['widget'].set_color(self.determine_light_color(light))
            
            # 🆕 Light状态文本提示
            state_text = f"{light['name']}  {'open' if light['on'] else 'close'}"
            light['widget'].set_label(state_text)

        for gauge in self.get_all_gauges():
            if 'default' not in gauge:
                gauge['widget'].set_label(gauge['name'])

       # 清除旧提示
        self.widgets['sysmon_alert'].set_text("")

        # 灯光状态检查提示
        f5 = self.parameters['lights']['1']
        f6 = self.parameters['lights']['2']
        if not f5['on']:
            self.widgets['sysmon_alert'].set_text("F5 should always turned on as green，press F5 to fix！")
            self.widgets['sysmon_alert'].set_color((255, 255, 0, 255))  # 黄色文字
        elif f6['on']:
            self.widgets['sysmon_alert'].set_text("F6 should keep shut off without red light，press F6 to fix！")
            self.widgets['sysmon_alert'].set_color((255, 255, 0, 255))  # 黄色文字
        # 刻度极限检查
        for scale_id, scale in self.parameters['scales'].items():
            widget = self.widgets.get(f'sysmon_scale_{scale["name"]}')
            if widget:
                if widget.value < 0.15 or widget.value > 0.85:
                    self.widgets['sysmon_alert'].set_text(f"{scale['name']}reach the limit，press{scale['key']}to fix！")


    def determine_light_color(self, light):
        color = light['oncolor'] if light['on'] == True else C['BACKGROUND']
        return color



    def start_failure(self, gauge):
        if gauge['_onfailure'] == True:
            pass  # TODO : warn in case of multiple failure on the same gauge
        else:
            gauge['_onfailure'] = True
            if 'default' in gauge.keys():  # Light case
                gauge['on'] = not gauge['default'] == 'on'
            else:  # Scale case
                if gauge['side'] not in [-1, 1]:
                    add = self.get_gauge_key(gauge) # Specify a gauge integer to generate
                                                    # a unique seed
                    gauge['side'] = choice([-1, 1], self.alias, self.scenario_time, int(add))
                gauge['_zone'] = gauge['side']
        gauge['failure'] = False
        # Schedule failure timing
        delay = self.parameters['automaticsolverdelay'] if self.parameters['automaticsolver'] \
            else self.parameters['alerttimeout']
        gauge['_failuretimer'] = delay

       
        #gauge_name = gauge['name']
        #tts_manager.speak(f"Failure detected on gauge {gauge_name}. Press {gauge_name} to resolve.") """
    
        import os
        gauge_name = gauge['name']
        letter = gauge_name[0].lower()
        number = gauge_name[1]
        sound_sequence = [
            'includes/sounds/english/male/normalized/failure.wav',
            f'includes/sounds/english/male/{letter}.wav',
            f'includes/sounds/english/male/{number}.wav',
            'includes/sounds/english/male/normalized/press.wav',
            f'includes/sounds/english/male/{letter}.wav',
            f'includes/sounds/english/male/{number}.wav',
            'includes/sounds/english/male/normalized/resolve.wav'
        ]
        if not hasattr(self, 'player'):
            from pyglet.media import Player
            self.player = Player()
        if self.player.playing:
            print("[Sysmon] Sound sequence is already playing, skipping new sequence.")
            return
        self.player.pause()
        self.player.next_source()  # Clear previous queue
        print(f"[Sysmon] Playing sound sequence: {sound_sequence}")
        for sound_path in sound_sequence:
            if os.path.exists(sound_path):
                print(f"[Sysmon] Found sound file: {sound_path}")
                try:
                    source = pyglet.media.load(sound_path, streaming=False)
                    self.player.queue(source)
                except Exception as e:
                    print(f"[Sysmon] Error loading sound {sound_path}: {e}")
            else:
                print(f"[Sysmon] Sound file not found: {sound_path}")
        self.player.play()
        # --- End of dynamic sound loading ---



    def stop_failure(self, gauge, success=False):
        # Reset the gauge failure timer
        gauge['_onfailure'] = False
        gauge['_failuretimer'] = None

        # Set the (potential) feedback type (ft)
        ft = 'positive' if self.parameters['automaticsolver'] or success == True else 'negative'

        # Does this feedback type (positive or negative) is currently active ?
        # If so, set the feedback type and duration, if the gauge has got one
        # (the feedback widget is refreshed by the refresh_widget method)
        if self.parameters['feedbacks'][ft]['active'] and '_feedbacktimer' in gauge:
            self.set_scale_feedback(gauge, ft)

        # Feed the freeze timer with feedback duration (1.5 by default) if the response is good
        if success:
            gauge['_freezetimer'] = self.parameters['feedbackduration']

        # IDEA: do we need to distinguish manual detection (hit) from automatic detection ?
        # Evaluate performance in terms of signal detection and response time
        if ft == 'positive':
            sdt_string, rt = 'HIT', gauge['_milliresponsetime']
        else:
            sdt_string, rt = 'MISS', float('nan')
        sdt_string = 'HIT' if ft == 'positive' else 'MISS'

        self.log_performance('name', gauge['name'])
        self.log_performance('signal_detection', sdt_string)
        self.log_performance('response_time', rt)

        # Reset gauge to its nominal (default) state
        if 'default' in gauge.keys():  # Light case
            gauge['on'] = gauge['default'] == 'on'
        else:  # Scale case
            gauge['_zone'] = 0
        gauge['_milliresponsetime'] = 0


    def get_gauges_key_value(self, key, value):
        gauge_list = list()
        for gauge in self.get_all_gauges():
            if gauge[key] == value:
                gauge_list.append(gauge)
        return gauge_list


    def get_gauge_by_key(self, key):
        return self.get_gauges_key_value('key', key)[0]


    def get_gauge_key(self, gauge):
        for key in ['lights', 'scales']:
            for k, v in self.parameters[key].items():
                if gauge == v:
                    return k


    def get_gauges_on_failure(self):
        return self.get_gauges_key_value('_onfailure', True)


    def get_scale_gauges(self):
        return [g for _,g in self.parameters['scales'].items()]


    def get_light_gauges(self):
        return [g for _,g in self.parameters['lights'].items()]


    def get_all_gauges(self):
        return [g for g in self.get_scale_gauges() + self.get_light_gauges()]


    def set_scale_feedback(self, gauge, feedback_type):
        # Set the feedback type and duration, if the gauge has got one
        # (the feedback widget is refreshed by the refresh_widget method)
        gauge['_feedbacktype'] = feedback_type
        gauge['_feedbacktimer'] = self.parameters['feedbackduration']


    def do_on_key(self, key, state, emulate):
        key = super().do_on_key(key, state, emulate)
        if key is None:
            return

        if state == 'press':
            gauge = self.get_gauge_by_key(key)
            if key in [g['key'] for g in self.get_gauges_on_failure()]:
                self.stop_failure(gauge=gauge, success=True)
            else:
                self.log_performance('name', gauge['name'])
                self.log_performance('signal_detection', 'FA')
                self.log_performance('response_time', float('nan'))

                # Set a negative feedback if relevant
                if self.parameters['feedbacks']['negative']['active']:
                    self.set_scale_feedback(gauge, 'negative')
