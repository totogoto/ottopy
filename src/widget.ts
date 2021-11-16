// Copyright (c) Indresh Vishwakarma
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

// Import the CSS
import '../css/widget.css';
import { WorldModel } from './models/world_model';
import $ from 'jquery';

import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 1 });
//Allowed method without valid maze
const ALLOWED_METHOD = ['halt', 'draw_all'];

export class MazeModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: MazeModel.model_name,
      _model_module: MazeModel.model_module,
      _model_module_version: MazeModel.model_module_version,
      _view_name: MazeModel.view_name,
      _view_module: MazeModel.view_module,
      _view_module_version: MazeModel.view_module_version,
      current_call: '{}',
      method_return: '{}',
      zoom: 1,
      floating: false,
      is_inited: false,
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any extra serializers here
  };

  static model_name = 'MazeModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'MazeView'; // Set to null if no view
  static view_module = MODULE_NAME; // Set to null if no view
  static view_module_version = MODULE_VERSION;
}

export class MazeView extends DOMWidgetView {
  world_model: WorldModel;

  method_changed = () => {
    let current_call: {
      method_name: string;
      params: any;
      cb: any;
      stats?: any;
      ui_id: string;
    } = JSON.parse(this.model.get('current_call'));

    console.log(
      `#${current_call.ui_id} need to call current_method: ${current_call.method_name}`
    );

    if (!current_call.method_name) {
      console.log('clearing queue');
      queue.clear();
    }

    this.report_stats(current_call.stats);
    if (current_call.method_name === 'halt') {
      return this.halt();
    } else {
      queue.add(() => {
        return new Promise((resolve) => {
          let ret =
            typeof this[current_call.method_name as keyof MazeView] ===
            'function'
              ? this[current_call.method_name as keyof MazeView].apply(
                  this,
                  current_call.params
                )
              : null;

          if (
            !ALLOWED_METHOD.some((e) => e === current_call.method_name) &&
            !$(`#${current_call.ui_id}`).length
          ) {
            console.log(
              'maze is not loaded or invalid id: ',
              current_call.ui_id,
              current_call.method_name,
              current_call.method_name in ALLOWED_METHOD
            );
            return resolve(null);
          }

          console.log('current_call in promise -> new code', current_call);
          let that = this;
          Promise.resolve(ret)
            .then(function (x) {
              // console.log("reached in promise");
              let data = JSON.stringify({
                value: x,
                cb: +new Date(),
                params: current_call.params,
                method: current_call.method_name,
              });
              console.log('setting return', data);
              that.model.set('method_return', data);
              that.model.save_changes();
              return data;
            })
            .then(resolve)
            .catch((err) => {
              console.log(
                'error =>',
                current_call.method_name,
                'execution failed',
                err
              );
            });
        });
      });
    }
  };

  draw_all = (
    world_config: any,
    ui_id: string,
    rows: number,
    cols: number,
    vwalls: [],
    hwalls: [],
    robots = [],
    objects: any = {},
    tileMap: any = {},
    tiles: any = [],
    messages: any = {},
    flags: any = {},
    pending_goals: any = [],
    drop_goals: any = []
  ) => {
    this.world_model.init(
      world_config,
      ui_id,
      rows,
      cols,
      vwalls,
      hwalls,
      robots,
      objects,
      tileMap,
      tiles,
      messages,
      flags,
      pending_goals,
      drop_goals
    );

    return this.sleepUntil(() => {
      return (
        this.world_model &&
        this.world_model.robots &&
        this.world_model.robots[0] &&
        this.world_model.robots[0].node
      );
    }, 3000);
  };

  sleepUntil = (f: Function, timeoutMs: number) => {
    return new Promise((resolve, reject) => {
      let timeWas: Date = new Date();
      let wait = setInterval(function () {
        if (f()) {
          clearInterval(wait);
          resolve('robo init done');
        } else if (new Date().getTime() - timeWas.getTime() > timeoutMs) {
          // Timeout

          clearInterval(wait);
          reject('error in robo init');
        }
      }, 20);
    });
  };

  halt = () => {
    console.log('halting and clearing queue');
    return queue.clear();
  };

  move_to = (index: number, x: number, y: number) => {
    return this.world_model && this.world_model.robots[index]?.move_to(x, y);
  };

  report_stats = (stats: any) => {
    return (
      this.world_model &&
      this.world_model.update_stats &&
      this.world_model.update_stats(stats)
    );
  };

  turn_left = (index: number) => {
    return (
      this.world_model &&
      this.world_model.robots &&
      this.world_model.robots.length > 0 &&
      this.world_model.robots[index]?.turn_left()
    );
  };

  set_trace = (index: number, color: string) => {
    return (
      this.world_model &&
      this.world_model.robots &&
      this.world_model.robots.length > 0 &&
      this.world_model.robots[index]?.set_trace(color)
    );
  };

  set_speed = (index: number, speed: number) => {
    return (
      this.world_model &&
      this.world_model.robots &&
      this.world_model.robots.length > 0 &&
      this.world_model.robots[index]?.set_speed(speed)
    );
  };

  add_wall = (x: number, y: number, dir: string) => {
    return this.world_model.draw_wall(x, y, dir);
  };

  add_object = (x: number, y: number, obj_name: string, val: number) => {
    return this.world_model.draw_object(x, y, { [obj_name]: val });
  };

  add_goal_object = (x: number, y: number, obj_name: string, val: number) => {
    return this.world_model.draw_custom(obj_name, x, y, val, true);
  };

  update_object = (x: number, y: number, val: number) => {
    return this.world_model.update_object(x, y, val);
  };

  remove_object = (x: number, y: number) => {
    return this.world_model.remove_object(x, y);
  };

  remove_flag = (x: number, y: number) => {
    return this.world_model.remove_object(x, y);
  };

  remove_wall = (x: number, y: number, dir: string) => {
    return this.world_model.remove_wall(x, y, dir);
  };

  set_succes_msg = (msg: string[]) => {
    return this.world_model && this.world_model.success_msg(msg);
  };

  error = (msg: string | string[]) => {
    let arr: string[] = [];
    return (
      this.world_model &&
      this.world_model.alert(arr.concat(msg).join(', '), 'danger')
    );
  };

  show_message = (
    msg: string,
    waitFor: number = 1,
    img: string = 'envelope'
  ) => {
    return this.world_model.read_message(msg, waitFor);
  };

  handle_zoom_level(zoom_level: number) {
    this.model.set('zoom', zoom_level);
    this.model.save_changes();
  }

  setInited() {
    console.log('widget inited set');
    this.model.set('is_inited', true);
    this.model.save_changes();
  }

  render() {
    this.method_changed();
    this.listenTo(this.model, 'change:current_call', this.method_changed);

    if (!this.world_model) {
      this.world_model = new WorldModel(
        this.model.get('zoom') || 1,
        this.handle_zoom_level.bind(this)
      );
    }
    this.initOutput();

    //set methods
    if (!this.model.get('is_inited')) {
      this.setInited();
    }
  }

  initOutput() {
    if ($('#outputArea').length === 0) {
      const $parent =
        this.model.get('floating') || false ? $('body') : $(this.el);

      let $outputArea = $(
        `<div id="outputArea" class="${
          this.model.get('floating') ? 'floating' : 'non-floating'
        }" />`
      );
      $parent.append($outputArea);
    }
  }
}
