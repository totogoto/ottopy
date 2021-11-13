import Konva from 'konva';
import { RobotModel } from './robot_model';
import $ from 'jquery';
import _isNumber from 'lodash/isNumber';
import _random from 'lodash/random';
import _padStart from 'lodash/padStart';

import draggable from '../utils/draggable';

const MIN_BOX_SIZE = 23;
const MAX_ROWS = 15;
const MAX_COLS = 15;
const LEFT_PADDING = 50;
export const NUMBER_PADDING = 30;
export const IMAGE_PADDING = 3;
const MARGIN_NUMBER_CIRCLE = 2;
const DEFAULT_HEIGHT = 500;
const MIN_HEIGHT = 450;
const MAX_BOX_SIZE = 50;

const walls_config: { [key: string]: any } = {
  normal: {
    stroke: 'darkred',
    strokeWidth: 5,
  },

  removable: {
    stroke: '#de1738',
    strokeWidth: 5,
  },

  goal: {
    stroke: 'darkred',
    strokeWidth: 7,
    dash: [5, 5],
  },
};
type WorldConfig = {
  border_color: string;
  grid_line_color: string;
  floating: boolean;
};
export class WorldModel {
  config: WorldConfig;
  ui_id: string;
  rows: number;
  cols: number;
  vwalls: any;
  hwalls: any;
  robots: any;
  width: number;
  height: number;
  bs: number;
  image_area: number;
  objects: any;
  tileMap: any;
  tiles: any;
  wrapper: HTMLDivElement;
  messages: any;
  pending_goals: any;
  drop_goals: any;
  flags: any;
  draggable: boolean;
  stats: {
    basket?: any;
    current_load?: number;
    max_capacity?: null | number;
    total_moves?: number;
  };
  ui: {
    stage: Konva.Stage;
    layers: {
      main: Konva.Layer;
      line: Konva.Layer;
      msg?: Konva.Layer;
      bg: Konva.Layer;
    };
  };
  current_run: JQuery<HTMLElement>;
  onZoomChange: Function;
  zoom_level: number;

  constructor(zoom_level: number, onZoomChange: Function) {
    this.onZoomChange = onZoomChange;
    this.zoom_level = zoom_level;
  }

  init(
    config: WorldConfig,
    ui_id: string,
    rows: number,
    cols: number,
    vwalls = [],
    hwalls = [],
    robots = [],
    objects = {},
    tileMap = {},
    tiles = [],
    messages = {},
    flags = {},
    pending_goals = [],
    drop_goals = []
  ) {
    this.robots = robots.map(
      (robot: RobotModel, i: number) =>
        new RobotModel(
          i,
          this,
          robot.x,
          robot.y,
          robot.orientation,
          robot.image
        )
    );
    this.draggable = false;
    this.rows = Math.min(MAX_ROWS, rows);
    this.cols = Math.min(MAX_COLS, cols);
    this.vwalls = vwalls;
    this.hwalls = hwalls;
    this.config = config;
    this.ui_id = ui_id;
    let screen_height = $(window).height() || DEFAULT_HEIGHT;
    let grid_height = Math.max(screen_height * 0.6, MIN_HEIGHT);

    this.bs = Math.ceil(
      Math.max(
        Math.min(grid_height / Math.max(this.rows, this.cols), MAX_BOX_SIZE),
        MIN_BOX_SIZE
      )
    );

    this.image_area = this.bs - 2 * IMAGE_PADDING;

    this.height = rows * this.bs;
    this.width = cols * this.bs;
    this.objects = objects;
    this.tileMap = tileMap;
    this.tiles = tiles;
    this.pending_goals = pending_goals;
    this.drop_goals = drop_goals;
    this.messages = messages;
    this.flags = flags;

    this.init_with_id(this.ui_id);
  }

  incrementZoom() {
    let classess = this.getZoomClasses();
    let classessToRemove = classess.join(' ');
    let nextClass = Math.max(...classess.map((x) => parseInt(x.split('-')[1])));

    if (nextClass < 10) {
      this.onZoomChange(nextClass / 10.0);
      $('.grid-slider', this.current_run)
        .removeClass(classessToRemove)
        .addClass(`zoom-${nextClass + 1}`);
    }
  }

  decrementZoom() {
    let classess = this.getZoomClasses();
    let classessToRemove = classess.join(' ');
    let nextClass = Math.min(...classess.map((x) => parseInt(x.split('-')[1])));
    this.onZoomChange(nextClass / 10.0);
    if (nextClass > 1) {
      $('.grid-slider', this.current_run)
        .removeClass(classessToRemove)
        .addClass(`zoom-${nextClass - 1}`);
    }
  }

  getZoomClasses() {
    let $outputArea = $('.grid-slider', this.current_run);
    let classess = $outputArea.attr('class')?.split(' ') || ['zoom-10'];
    return classess.filter((x) => x.startsWith('zoom-'));
  }

  init_output_window() {
    let $outputArea = $('#outputArea');

    let $currentRun = this.current_run;
    $currentRun.append(this.skeleton());
    let that = this;
    //button actions
    $('.output-action-toggle', $currentRun).on('click', function () {
      console.log('clicked button');
      if ($(this).html() == 'ᐁ') {
        $(this).html('ᐅ');
      } else {
        $(this).html('ᐁ');
      }
      $('.grid-slider', $currentRun).slideToggle();
    });

    $('.output-action-zoom-in', $currentRun).on('click', function () {
      that.incrementZoom();
    });

    $('.output-action-zoom-out', $currentRun).on('click', function () {
      that.decrementZoom();
    });

    //Draggble $current_run
    if (this.config.floating && !this.draggable) {
      draggable($outputArea[0]);
      this.draggable = true;
    }

    if (!this.config.floating) {
      $outputArea[0].onmousedown = null;
    }
  }

  init_with_id(ui_id: string) {
    let $outputArea = $('#outputArea');
    this.current_run = $(`#${this.ui_id}`, $outputArea);

    //clean up
    $('.run_output', $outputArea).not(this.current_run).remove();

    if (this.current_run.length === 0) {
      console.log('in the run');
      this.current_run = $(`<div id=${this.ui_id} class='run_output'> </div>`);
      $outputArea.append(this.current_run);

      this.init_output_window();
      this.draw_canvas();
    }
  }

  skeleton() {
    return `
      <div class="output-header clr-info">
        <div class="output-header-msg"></div>
        <div class="output-actions btn-group">
          <button class="output-action-zoom-in">&plus;</button>
          <button class="output-action-zoom-out">&minus;</button>
          <button class="output-action-toggle">ᐁ</button>
        </div>
      </div>   
      <div class="grid-slider zoom-${this.zoom_level * 10}">
        <div class="grid">
          <div class="stats">
            <div class="stats-item">
              <div class="stats-title">Taken Moves</div>
              <div class="no_of_steps stats-value">0</div> 
            </div>
            <div class="stats-item">
              <div class="stats-title">current load</div>
              <div class="current_load stats-value">0</div> 
            </div>
            <div class="stats-item">
              <div class="stats-title">capacity</div>
              <div class="capacity stats-value">Unlimited</div> 
            </div>
          </div>
          <div class="konva-body">
            <div class="konva-grid"></div>
          </div>
        </div>
      </div>
    `;
  }

  draw_canvas() {
    try {
      let stage = new Konva.Stage({
        container: '.konva-grid',
        width: this.width + NUMBER_PADDING,
        height: this.height + NUMBER_PADDING,
      });

      this.ui = {
        stage: stage,
        layers: {
          bg: new Konva.Layer(),
          main: new Konva.Layer({ offsetX: -1 * NUMBER_PADDING }),
          line: new Konva.Layer(),
        },
      };

      this.robots[0].init_canvas();
      this.robots[0].draw();

      stage.add(this.ui.layers.bg);
      stage.add(this.ui.layers.main);
      stage.add(this.ui.layers.line);

      this.draw_border();
      this.draw_grid();
      this.draw_objects();
      this.draw_stats();
      this.draw_envelops();
      this.draw_flags();
      this.draw_drop_goals(this.drop_goals);
      return this.ui.layers.main.draw();
    } catch (error) {
      console.log(
        '🚀 ~ file: world_model.ts ~ line 238 ~ WorldModel ~ draw_canvas ~ error',
        error
      );

      return Promise.resolve(error);
    }
  }

  draw_stats() {
    let vals = [
      this.stats.total_moves,
      this.stats.current_load,
      this.stats.max_capacity || 'Unlimited',
    ];

    //@ts-ignore
    $('.stats-value').text(function (i) {
      return vals[i];
    });
  }

  alert(
    msg: string,
    type: 'info' | 'success' | 'danger' = 'info',
    waitFor: number = 3000
  ) {
    const classToRemove = ['info', 'success', 'danger']
      .filter((x) => x !== type)
      .map((x) => `clr-${x}`)
      .join(' ');

    $('.output-header', this.current_run)
      .removeClass(classToRemove)
      .addClass(`clr-${type}`);

    return $('.output-header-msg', this.current_run)
      .text(msg)
      .css({ opacity: 1 })
      .animate({
        width: 'show',
        duration: waitFor,
      });
  }

  success_msg(msg: string | string[]) {
    let arr: string[] = [];
    return this.alert(arr.concat(msg).join(','), 'success');
  }

  draw_objects() {
    for (const key in this.objects) {
      const [x, y] = key.split(',').map((zz) => parseInt(zz));
      this.draw_object(x, y, this.objects[key]);
    }
  }

  draw_flags() {
    for (const key in this.flags) {
      const [x, y] = key.split(',').map((zz) => parseInt(zz));
      this.draw_flag(x, y);
    }
  }

  draw_flag(x: number, y: number) {
    this.draw_custom('racing_flag_small', x, y, 0);
  }

  draw_object(x: number, y: number, obj: any) {
    for (const obj_name in obj) {
      let val = this.parse_value(obj[obj_name]);

      if (obj_name === 'beeper') {
        this.draw_beeper(x, y, val);
      } else {
        this.draw_custom(obj_name, x, y, val);
      }
    }
  }

  draw_envelops() {
    for (const key in this.messages) {
      const [x, y] = key.split(',').map((zz) => parseInt(zz));
      this.draw_envelop(x, y, this.messages[key]);
    }
  }

  draw_envelop(x: number, y: number, message: string) {
    this.draw_custom('envelope', x, y);
  }

  update_object(x: number, y: number, val: number) {
    let text = this.ui.layers.main.find(`.obj-${x}-${y}-text`)[0];
    if (text) {
      //@ts-ignore
      text.text(`${val}`);
      this.ui.layers.main.draw();
    }
  }

  draw_beeper(x: number, y: number, val: number) {
    let radius = (0.6 * this.bs) / 2;
    let [cx, cy] = this.point2cxy(x, y);
    cx = cx + this.bs / 2;
    cy = cy - this.bs / 2;
    let fontSize = Math.ceil((this.bs * 18) / 50);
    let circle = new Konva.Circle({
      radius: radius,
      x: cx,
      y: cy,
      fill: 'yellow',
      stroke: 'orange',
      strokeWidth: 5,
      name: `obj-${x}-${y}-circle`,
    });

    let num = new Konva.Text({
      text: `${val}`,
      x: cx - circle.radius() / 2,
      y: cy - circle.radius() / 2,
      fontSize: fontSize,

      name: `obj-${x}-${y}-text`,
    });

    this.ui.layers.main.add(circle, num);
  }

  remove_object(x: number, y: number) {
    if (!this.ui) {
      return;
    }

    let circle = this.ui.layers.main.find(`.obj-${x}-${y}-circle`)[0];
    let text = this.ui.layers.main.find(`.obj-${x}-${y}-text`)[0];
    let img = this.ui.layers.main.find(`.obj-${x}-${y}-img`)[0];

    if (circle) {
      //@ts-ignore
      circle.destroy();
    }
    if (text) {
      //@ts-ignore
      text.destroy();
    }
    if (img) {
      //@ts-ignore
      img.destroy();
    }

    this.ui.layers.main.draw();
  }

  //not touched yet to fix
  draw_sprite(sprite_name: string, x: number, y: number, frameRate = 1) {
    let spritePath = this.tileMap[sprite_name];
    let [cx, cy] = this.point2cxy(x, y);
    let sprite = new Image();
    sprite.src = spritePath;
    const animations = {
      motion: [0, 0, 40, 40, 40, 0, 40, 40],
    };
    let that = this;
    sprite.onload = function () {
      let imageSprite = new Konva.Sprite({
        x: cx + LEFT_PADDING,
        y: cy - that.bs / 2,
        name: `sprite-${x}-${y}-img`,
        image: sprite,
        animation: 'motion',
        animations: animations,
        frameRate: frameRate,
      });

      that.ui.layers.main.add(imageSprite);
      that.ui.layers.main.batchDraw();
      imageSprite.start();
    };
  }

  draw_custom(
    obj_name: string,
    x: number,
    y: number,
    val: any = null,
    isGoal: boolean = false
  ) {
    let imagePath = this.tileMap[obj_name];
    let [cx, cy] = this.point2cxy(x, y + 1);

    let radius = (0.4 * this.bs) / 2;
    let group = new Konva.Group({
      x: cx + (this.bs - radius) - MARGIN_NUMBER_CIRCLE,
      y: cy + (this.bs - radius) - MARGIN_NUMBER_CIRCLE,
    });

    if (!isGoal && !!val) {
      let circle = new Konva.Circle({
        radius: radius,
        fill: 'white',
        stroke: '#aaa',
        opacity: 0.9,
      });

      let TEXT_MARGIN =
        val > 9 ? MARGIN_NUMBER_CIRCLE : 2 * MARGIN_NUMBER_CIRCLE;
      let fontSize = Math.ceil((this.bs * 14) / 50); // when bs = 50 fontSize=14
      let num = new Konva.Text({
        text: `${val}`,
        fontSize: fontSize,
        name: `obj-${x}-${y}-text`,
        offsetX: circle.x() + radius - TEXT_MARGIN,
        offsetY: circle.y() + radius - TEXT_MARGIN,
      });
      group.add(circle, num);
    }

    Konva.Image.fromURL(imagePath, (node: Konva.Image) => {
      node.setAttrs({
        x: cx + IMAGE_PADDING,
        y: cy + IMAGE_PADDING,
        width: this.image_area,
        height: this.image_area,
        name: `obj-${x}-${y}-img`,
      });

      if (isGoal) {
        node.cache();
        node.filters([Konva.Filters.Grayscale]);
        this.ui.layers.main.add(node);
      } else {
        this.ui.layers.main.add(node);
        this.ui.layers.main.add(group);
      }
      this.ui.layers.main.batchDraw();
    });
  }

  draw_drop_goals(goals = []) {
    goals.map((goal) => {
      //@ts-ignore
      this.draw_custom(goal.obj_name, goal.x, goal.y, goal.val, true);
    });
  }

  update_stats(stats = {}) {
    this.stats = stats;
    this.draw_stats();
  }

  parse_value(val: number | string) {
    if (!val) return 0;
    if (_isNumber(val)) return val;
    else {
      const [min_val, max_val] = val.split('-').map((zz) => parseInt(zz));
      return _random(min_val, max_val);
    }
  }

  draw_border() {
    let box = new Konva.Rect({
      stroke: this.config.border_color,
      strokeWidth: 5,
      closed: true,
      width: this.width,
      height: this.height,
    });

    console.log(
      '🚀 ~ file: world_model.ts ~ line 585 ~ WorldModel ~ draw_border ~ this.height',
      this.height
    );

    this.ui.layers.main.add(box);
  }

  draw_grid() {
    this.draw_cols();
    this.draw_rows();
    this.draw_walls();
    this.draw_tiles();
  }

  _draw_tile(x: number, y: number, tile: string) {
    let [cx, cy] = this.point2cxy(x, y + 1);
    let imagePath = this.tileMap[tile];
    Konva.Image.fromURL(imagePath, (node: Konva.Image) => {
      node.setAttrs({
        x: cx + NUMBER_PADDING,
        y: cy,
        width: this.bs,
        height: this.bs,
        name: `obj-${x}-${y}-tilebg`,
      });
      this.ui.layers.bg.add(node);
      this.ui.layers.bg.batchDraw();
    });
  }

  draw_tiles() {
    this.tiles.forEach((list: any, row: number) => {
      list.forEach((tile: any, col: number) => {
        if (!!tile) {
          this._draw_tile(row + 1, col + 1, tile);
        }
      });
    });
  }

  draw_cols() {
    const BOX_TO_NUM_PADDING = 10;
    for (let col = 1; col < this.cols; col++) {
      let line = new Konva.Line({
        stroke: this.config.grid_line_color,
        points: [col * this.bs, 2.5, col * this.bs, this.height - 2.5],
      });

      let count = new Konva.Text({
        text: `${col}`,
        y: this.height + BOX_TO_NUM_PADDING,
        x: (col - 1) * this.bs + this.bs / 4,
      });

      this.ui.layers.main.add(line, count);
    }

    let last_count = new Konva.Text({
      text: `${this.cols}`,
      y: this.height + BOX_TO_NUM_PADDING,
      x: (this.cols - 1) * this.bs + this.bs / 4,
    });

    this.ui.layers.main.add(last_count);
  }

  draw_rows() {
    for (let row = 1; row < this.rows; row++) {
      let line = new Konva.Line({
        stroke: this.config.grid_line_color,
        points: [this.width - 2.5, row * this.bs, 2.5, row * this.bs],
      });

      let count = new Konva.Text({
        text: `${this.rows + 1 - row}`,
        y: row * this.bs,
        offsetY: this.bs * 0.75,
        offsetX: 20,
      });

      this.ui.layers.main.add(line, count);
    }

    let last_count = new Konva.Text({
      text: `1`,
      y: this.rows * this.bs,
      offsetY: this.bs * 0.75,
      offsetX: 20,
    });

    this.ui.layers.main.add(last_count);
  }

  point2cxy(x: number, y: number) {
    return [(x - 1) * this.bs, this.height - (y - 1) * this.bs];
  }

  draw_wall(x: number, y: number, dir: string, wall_type: string = 'normal') {
    let config = walls_config[wall_type];
    let border = null;
    let [cx, cy] = this.point2cxy(x, y);
    if (dir === 'east') {
      border = new Konva.Line({
        ...config,
        name: `vwall-${x}-${y}`,
        points: [cx + this.bs, cy - this.bs, cx + this.bs, cy],
      });
    }

    if (dir === 'north') {
      border = new Konva.Line({
        name: `hwall-${x}-${y}`,
        ...config,
        points: [cx, cy - this.bs, cx + this.bs, cy - this.bs],
      });
    }

    if (border) this.ui.layers.main.add(border);
  }

  read_message(msg: string, waitFor = 3) {
    return this.alert(`🤖: ${msg}`, 'info', waitFor * 1000);
  }

  remove_wall(x: number, y: number, dir: string) {
    if (dir !== 'north' && dir !== 'east') return;
    let wall = this.ui.layers.main.find(
      `.${dir === 'north' ? 'hwall' : 'vwall'}-${x}-${y}`
    )[0];
    if (wall) {
      wall.destroy();
    }
    this.ui.layers.main.draw();
  }

  draw_typed_wall(x: number, y: number, dir: string, val: number) {
    let [isGoal, isRemovable, isWall] = _padStart(
      Number(val).toString(2),
      3,
      '0'
    );

    if (parseInt(isWall)) {
      if (parseInt(isRemovable)) {
        this.draw_wall(x, y, dir, 'removable');
      } else {
        this.draw_wall(x, y, dir, 'normal');
      }
    } else if (parseInt(isGoal)) {
      this.draw_wall(x, y, dir, 'goal');
    }
  }

  draw_walls() {
    this.hwalls.forEach((hw: any, i: number) => {
      hw.forEach((val: number, j: number) => {
        if (val) {
          this.draw_typed_wall(i, j, 'north', val);
        } else {
          this.remove_wall(i, j, 'north');
        }
      });
    });

    this.vwalls.forEach((vw: any, i: number) => {
      vw.forEach((val: number, j: number) => {
        if (val) {
          this.draw_typed_wall(i, j, 'east', val);
        } else {
          this.remove_wall(i, j, 'east');
        }
      });
    });
  }
}
