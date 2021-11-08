import Konva from 'konva';
import { WorldModel, NUMBER_PADDING, IMAGE_PADDING } from './world_model';

const mod = (n: number, m: number) => {
  return ((n % m) + m) % m;
};

const _directions = [
  [1, -1],
  [1, 1],
  [-1, 1],
  [-1, -1],
];

// const rotationFix = [
//   [0, 0],
//   [0, -1],
//   [1, -1],
//   [1, 0],
// ];

export const orientation_hash = {
  EAST: 0,
  NORTH: 1,
  WEST: 2,
  SOUTH: 3,
};

const robot_svg = `<svg xmlns="http://www.w3.org/2000/svg" version="1.1" class="svg-triangle" width='100' height='100' fill="#008080">
<path d="M 95,50 5,95 5,5 z"/>
</svg>`;

export class RobotModel {
  x: number;
  index: number;
  y: number;
  orientation: number;
  image?: string;
  canvas: Konva.Layer;
  node: Konva.Image | Konva.Path;
  points: any = [];
  traceColor: string = 'red';
  speed: number = 1;
  bs: number;
  rotation_diff: any;

  world: WorldModel;

  constructor(
    index: number,
    world: WorldModel,
    x: number,
    y: number,
    orientation: number,
    image?: string
  ) {
    this.index = index;
    this.x = x;
    this.y = y;
    this.orientation = orientation;
    this.image = image;
    this.world = world;
    this.speed = 0.1;
    this.rotation_diff = { x: 0, y: 0 };
    this.bs = this.world.bs;
  }

  init_canvas() {
    this.canvas = this.world.ui.layers.main;
  }

  cr2xy(x: number, y: number) {
    let [cx, cy] = this.world.point2cxy(x, y + 1);
    return [cx, cy];
  }

  trace_point(x: number, y: number) {
    let [cx, cy] = this.cr2xy(x, y - 1);
    let direction_vector = _directions[this.orientation];
    let scale = this.world.bs * 0.1;
    let xx = cx + (this.world.bs / 2.0 + scale * direction_vector[0]);
    let yy = cy - (this.world.bs / 2.0 + scale * direction_vector[1]);

    return [xx, yy];
  }

  draw_trace() {
    let trace = new Konva.Line({
      points: this.points.slice(Math.max(this.points.length - 4, 0)),
      stroke: this.traceColor,
      offsetX: -NUMBER_PADDING,
    });
    if (
      this.world &&
      this.world.ui &&
      this.world.ui.layers &&
      this.world.ui.layers.line
    ) {
      this.world.ui.layers.line.add(trace);
      this.world.ui.layers.line.draw();
    }
  }

  add_point(x: number, y: number) {
    const [tx, ty] = this.trace_point(x, y);
    this.points = this.points.concat([tx, ty]);
    this.draw_trace();
  }

  set_trace(color: string) {
    this.traceColor = color;
    this.add_point(this.x, this.y);
  }

  set_speed(speed: number) {
    this.speed = speed;
  }

  clear_trace() {
    this.points = [];
    if (
      this.world &&
      this.world.ui &&
      this.world.ui.layers &&
      this.world.ui.layers.line
    ) {
      this.world.ui.layers.line.destroyChildren();
      this.world.ui.layers.line.draw();
    }
  }

  move_to = (x: number, y: number) => {
    return new Promise((resolve) => {
      let [cx, cy] = this.cr2xy(x, y);

      let tween = new Konva.Tween({
        node: this.node,
        x: cx + IMAGE_PADDING + this.node.width() / 2,
        y: cy + IMAGE_PADDING + this.node.height() / 2,
        offsetX: this.node.width() / 2,
        offsetY: this.node.height() / 2,
        duration: this.speed,
        onFinish: () => {
          this.x = x;
          this.y = y;
          console.log('finished', x, y);
          this.add_point(x, y);
          resolve('done');
        },
      });

      tween.play();
    });
  };

  rotate_node = (node: Konva.Node, rotation: number) => {
    const degToRad = Math.PI / 180;

    const rotatePoint = ({ x, y }: any, deg: number) => {
      const rcos = Math.cos(deg * degToRad),
        rsin = Math.sin(deg * degToRad);
      return { x: x * rcos - y * rsin, y: y * rcos + x * rsin };
    };

    //current rotation origin (0, 0) relative to desired origin - center (node.width()/2, node.height()/2)
    const displayedWidth = node.width() * node.scaleX();
    const displayedHeight = node.height() * node.scaleY();
    const topLeft = { x: -displayedWidth / 2, y: -displayedHeight / 2 };
    const current = rotatePoint(topLeft, node.rotation());
    const rotated = rotatePoint(topLeft, rotation);
    const dx = rotated.x - current.x,
      dy = rotated.y - current.y;

    return {
      x: dx,
      y: dy,
      rotation,
    };
  };

  turn_left = () => {
    return new Promise((resolve) => {
      this.orientation = mod(this.orientation + 1, 4);
      // let [cx, cy] = this.cr2xy(this.x, this.y);
      this.rotation_diff = this.rotate_node(
        this.node,
        mod(-90 * this.orientation, 360)
      );

      let tween = new Konva.Tween({
        node: this.node,
        rotation: this.rotation_diff.rotation,
        duration: this.speed,
        // x: this.node.x() + this.rotation_diff.x,
        // y: this.node.y() + this.rotation_diff.y,
        onFinish: () => {
          this.add_point(this.x, this.y);
          console.log('finished', this.x, this.y);
          resolve('done');
        },
      });

      tween.play();
    });
  };

  draw() {
    let [cx, cy] = this.cr2xy(this.x, this.y);

    if (this.image) {
      Konva.Image.fromURL(this.image, (node: Konva.Image) => {
        this.rotation_diff = this.rotate_node(node, -(this.orientation * 90));
        node.setAttrs({
          x: cx,
          y: cy,
          width: this.world.image_area,
          height: this.world.image_area,
          rotation: -(this.orientation * 90),
        });
        this.node = node;

        this.canvas.add(this.node);
        this.canvas.batchDraw();
      });
    } else {
      let svg64 = btoa(robot_svg);
      var b64Start = 'data:image/svg+xml;base64,';
      var image64 = b64Start + svg64;

      Konva.Image.fromURL(image64, (node: Konva.Image) => {
        node.setAttrs({
          x: cx + IMAGE_PADDING,
          y: cy + IMAGE_PADDING,
          width: this.world.image_area,
          height: this.world.image_area,
          rotation: -(this.orientation * 90),
        });

        node.offsetX(node.width() / 2);
        node.offsetY(node.height() / 2);
        node.x(node.x() + node.width() / 2);
        node.y(node.y() + node.height() / 2);

        this.node = node;
        this.canvas.add(this.node);
        this.canvas.batchDraw();
      });
    }
  }
}
