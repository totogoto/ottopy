#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Indresh Vishwakarma.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import DOMWidget
from traitlets import Unicode, Bool, Float, observe
from ._frontend import module_name, module_version
from IPython.display import HTML as html_print
from IPython.display import display
import copy

import time as _time
from datetime import datetime
import json

from .robot import Robot

global zoom_level
zoom_level = 1.0


def cstr(s, color='black'):
    return "<div style='background:#FFFFC8;padding: 10px'> <text style=color:{}>{}</text></div>".format(color, s)


def print_desc(msg, color="black"):
    if msg is not None:
        display(html_print(cstr(msg, color=color)))


class Maze(DOMWidget):
    """TODO: Add docstring here
    """
    _model_name = Unicode('MazeModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('MazeView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    current_call = Unicode('{}').tag(sync=True)
    method_return = Unicode('{}').tag(sync=True)
    floating = Bool(False).tag(sync=True)
    is_inited = Bool(False).tag(sync=True)

    zoom = Float(1.0).tag(sync=True)
    
    @observe('zoom')
    def _update_zoom_level(self, change):
        global zoom_level
        zoom_level = self.zoom

    def js_call(self, method_name, params):
        if self.is_inited == False:
            self.js_call_q.append([method_name, copy.deepcopy(params)])
        else:
            # clean the old queue
            if len(self.js_call_q) > 0:
                while len(self.js_call_q) > 0:
                    _call = self.js_call_q.pop(0)
                    self.execute_js_call(method_name=_call[0], params=_call[1])

            if method_name != "flush_js_q":
                self.execute_js_call(method_name=method_name, params=params)

    def execute_js_call(self, method_name, params):
        cb = datetime.now().strftime('%f')
        self.model.js_call_counter += 1
        if self.model.js_call_counter % 10 == 0:
            _time.sleep(0.50)

        if self.model.has_balance():
            bot = self.bot()
            stats = bot.stats.report() if bot is not None else {}

            self.current_call = json.dumps(
                {'method_name': method_name, 'params': params, 'cb': cb, 'stats': stats, 'ui_id': self.model.ui_id})
        else:
            self.current_call = json.dumps(
                {'method_name': 'halt', 'params': [], 'cb': cb, 'ui_id': self.model.ui_id})
            raise RuntimeError("Instruction Quota Exceeded")

    def __init__(self, model, floating=False, zoom=None):

        super(Maze, self).__init__()
        global zoom_level
        self.model = model
        self.floating = floating
        self.is_inited = False
        self.zoom = zoom or zoom_level
        self.robots = [Robot(idx, x, self)
                       for idx, x in enumerate(self.model.robots)]

        self.js_call_q = []
        self.init_time = datetime.now()

        display(self)
        self.model.render_all(self.js_call)

    def bot(self, bot_index=0):
        return self.robots[bot_index]

    def get_description(self):
        return self.model.description

    def print_description(self):
        print_desc(self.get_description())

    def check(self, bot_index=0):
        val = self.model.check(self.bot(bot_index))
        if val:
            self.js_call('set_succes_msg', ['🎉 Task Completed'])
        else:
            self.js_call('error', ["🤭 One Or More Goal are Not Completed."])
        return val
