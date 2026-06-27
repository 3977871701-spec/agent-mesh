import { Component, ComponentType, Wire, Net } from '../types';

/**
 * LED 闪烁电路 (NE555) 示例 - 简化版
 *
 * 布局说明：
 * - 所有器件使用整数坐标
 * - 导线连接到引脚的绝对位置
 * - 引脚位置 = 器件位置 + 引脚相对偏移
 */

/**
 * LED 闪烁电路数据
 * 简化版布局 - 器件整齐排列
 */
export function createLEDFlashingCircuitSimple(): {
  components: Omit<Component, 'id'>[];
  wires: Omit<Wire, 'id'>[];
  nets: Omit<Net, 'id'>[];
} {
  // ========== 器件定义 ==========
  // 使用简单的引脚 ID
  const components: Omit<Component, 'id'>[] = [];

  // IC1: NE555 定时器 - 中心位置 (300, 200)
  // 引脚定义：左列从上到下，右列从下到上
  const ic1Pins = [
    { id: 'ic1-p1', name: 'GND', number: '1', x: -50, y: -30, direction: 'power' as const },
    { id: 'ic1-p2', name: 'TRIG', number: '2', x: -50, y: -10, direction: 'in' as const },
    { id: 'ic1-p3', name: 'OUT', number: '3', x: -50, y: 10, direction: 'out' as const },
    { id: 'ic1-p4', name: 'RESET', number: '4', x: -50, y: 30, direction: 'in' as const },
    { id: 'ic1-p5', name: 'CTRL', number: '5', x: 50, y: 30, direction: 'in' as const },
    { id: 'ic1-p6', name: 'THRES', number: '6', x: 50, y: 10, direction: 'in' as const },
    { id: 'ic1-p7', name: 'DISCH', number: '7', x: 50, y: -10, direction: 'out' as const },
    { id: 'ic1-p8', name: 'VCC', number: '8', x: 50, y: -30, direction: 'power' as const },
  ];
  components.push({
    type: ComponentType.GENERIC_IC,
    reference: 'IC1',
    value: 'NE555',
    x: 300,
    y: 200,
    rotation: 0,
    pins: ic1Pins,
    properties: {},
  });

  // R1: 10kΩ - IC1 左上方
  const r1Pins = [
    { id: 'r1-p1', name: '1', number: '1', x: -25, y: 0, direction: 'bidirectional' as const },
    { id: 'r1-p2', name: '2', number: '2', x: 25, y: 0, direction: 'bidirectional' as const },
  ];
  components.push({
    type: ComponentType.RESISTOR,
    reference: 'R1',
    value: '10kΩ',
    x: 180,
    y: 130,
    rotation: 0,
    pins: r1Pins,
    properties: {},
  });

  // R2: 10kΩ - IC1 右下方
  const r2Pins = [
    { id: 'r2-p1', name: '1', number: '1', x: -25, y: 0, direction: 'bidirectional' as const },
    { id: 'r2-p2', name: '2', number: '2', x: 25, y: 0, direction: 'bidirectional' as const },
  ];
  components.push({
    type: ComponentType.RESISTOR,
    reference: 'R2',
    value: '10kΩ',
    x: 350,
    y: 300,
    rotation: 0,
    pins: r2Pins,
    properties: {},
  });

  // C1: 10uF - IC1 下方
  const c1Pins = [
    { id: 'c1-p1', name: '1', number: '1', x: -25, y: 0, direction: 'bidirectional' as const },
    { id: 'c1-p2', name: '2', number: '2', x: 25, y: 0, direction: 'bidirectional' as const },
  ];
  components.push({
    type: ComponentType.CAPACITOR,
    reference: 'C1',
    value: '10µF',
    x: 420,
    y: 300,
    rotation: 0,
    pins: c1Pins,
    properties: {},
  });

  // LED1: 红色 LED - 左侧
  const led1Pins = [
    { id: 'led1-p1', name: 'A', number: '1', x: -25, y: 0, direction: 'in' as const },
    { id: 'led1-p2', name: 'K', number: '2', x: 25, y: 0, direction: 'out' as const },
  ];
  components.push({
    type: ComponentType.LED,
    reference: 'LED1',
    value: 'Red',
    x: 120,
    y: 320,
    rotation: 90,
    pins: led1Pins,
    properties: {},
  });

  // R3: 330Ω - LED 上方
  const r3Pins = [
    { id: 'r3-p1', name: '1', number: '1', x: -25, y: 0, direction: 'bidirectional' as const },
    { id: 'r3-p2', name: '2', number: '2', x: 25, y: 0, direction: 'bidirectional' as const },
  ];
  components.push({
    type: ComponentType.RESISTOR,
    reference: 'R3',
    value: '330Ω',
    x: 120,
    y: 250,
    rotation: 0,
    pins: r3Pins,
    properties: {},
  });

  // VCC: 5V 电源 - 顶部
  const vccPins = [
    { id: 'vcc-p1', name: '+', number: '1', x: 0, y: -20, direction: 'power' as const },
    { id: 'vcc-p2', name: '-', number: '2', x: 0, y: 20, direction: 'power' as const },
  ];
  components.push({
    type: ComponentType.VOLTAGE_SOURCE,
    reference: 'V1',
    value: '5V',
    x: 300,
    y: 50,
    rotation: 0,
    pins: vccPins,
    properties: {},
  });

  // GND: 地符号 - 底部
  const gndPins = [
    { id: 'gnd-p1', name: 'GND', number: '1', x: 0, y: -15, direction: 'power' as const },
  ];
  components.push({
    type: ComponentType.GND,
    reference: 'GND',
    value: 'GND',
    x: 180,
    y: 420,
    rotation: 0,
    pins: gndPins,
    properties: {},
  });

  // GND2: 第二个地符号
  const gnd2Pins = [
    { id: 'gnd2-p1', name: 'GND', number: '1', x: 0, y: -15, direction: 'power' as const },
  ];
  components.push({
    type: ComponentType.GND,
    reference: 'GND2',
    value: 'GND',
    x: 500,
    y: 420,
    rotation: 0,
    pins: gnd2Pins,
    properties: {},
  });

  // ========== 导线定义 ==========
  // 导线 points 格式：[x1, y1, x2, y2, x3, y3, ...]
  // 每条导线连接两个或多个点

  const wires: Omit<Wire, 'id'>[] = [];

  // 1. VCC 电源到 IC1 pin 8 (VCC) 和 pin 4 (RESET)
  // VCC 引脚在 (300, 50)，其 '+' 引脚在 y: -20，所以位置是 (300, 30)
  // IC1 pin 8 在 (300+50, 200-30) = (350, 170)
  wires.push({
    points: [300, 30, 300, 50, 350, 50, 350, 170], // VCC 到 IC1 pin 8
  });

  // 2. IC1 pin 4 (RESET) 到 VCC 总线
  // IC1 pin 4 在 (300-50, 200+30) = (250, 230)
  wires.push({
    points: [250, 230, 250, 50, 300, 50], // IC1 RESET 到 VCC 总线
  });

  // 3. IC1 pin 1 (GND) 到 GND
  // IC1 pin 1 在 (300-50, 200-30) = (250, 170)
  wires.push({
    points: [250, 170, 250, 350, 180, 350, 180, 405], // IC1 GND 到 GND
  });

  // 4. R1 连接 IC1 pin 7 (DISCH) 到 VCC
  // IC1 pin 7 在 (300+50, 200-10) = (350, 190)
  // R1 在 (180, 130)，pin 2 在 (180+25, 130) = (205, 130)
  wires.push({
    points: [350, 190, 350, 130, 205, 130], // IC1 DISCH 到 R1 pin 2
  });

  // 5. R1 pin 1 连接到 IC1 pin 7 (通过 junction)
  // R1 pin 1 在 (180-25, 130) = (155, 130)
  wires.push({
    points: [155, 130, 155, 160, 350, 160, 350, 190], // R1 pin 1 到 IC1 DISCH (水平线)
  });

  // 6. R2 连接 IC1 pin 2 (TRIG) 和 pin 6 (THRES)
  // IC1 pin 2 在 (300-50, 200-10) = (250, 190)
  // IC1 pin 6 在 (300+50, 200+10) = (350, 210)
  // R2 在 (350, 300)，pin 1 在 (350-25, 300) = (325, 300)
  wires.push({
    points: [325, 300, 325, 190, 250, 190], // R2 pin 1 到 IC1 TRIG
  });

  wires.push({
    points: [325, 300, 325, 210, 350, 210], // R2 pin 1 到 IC1 THRES
  });

  // 7. C1 连接到 R2 和 GND
  // C1 在 (420, 300)，pin 1 在 (420-25, 300) = (395, 300)
  // C1 pin 2 在 (420+25, 300) = (445, 300)
  wires.push({
    points: [395, 300, 325, 300], // C1 pin 1 到 R2
  });

  wires.push({
    points: [445, 300, 500, 300, 500, 405], // C1 pin 2 到 GND2
  });

  // 8. IC1 pin 3 (OUT) 输出到 R3 和 LED
  // IC1 pin 3 在 (300-50, 200+10) = (250, 210)
  // R3 在 (120, 250)，pin 1 在 (120-25, 250) = (95, 250)
  wires.push({
    points: [250, 210, 95, 210, 95, 250], // IC1 OUT 到 R3 pin 1
  });

  // 9. R3 pin 2 到 LED
  // R3 pin 2 在 (120+25, 250) = (145, 250)
  // LED 在 (120, 320)，rotation 90，pin A 在 (-25*cos-0*sin, -25*sin+0*cos) + (120,320) = (120, 295)
  wires.push({
    points: [145, 250, 120, 250, 120, 295], // R3 pin 2 到 LED A (水平线 + 垂直线)
  });

  // 10. LED K 到 GND
  // LED pin K 在 y: +25，位置 (120, 320+25) = (120, 345)
  wires.push({
    points: [120, 345, 120, 405], // LED K 到 GND
  });

  // 11. IC1 pin 5 (CTRL) 通过小电容接地
  // IC1 pin 5 在 (300+50, 200+30) = (350, 230)
  wires.push({
    points: [350, 230, 380, 230, 380, 260], // IC1 CTRL 水平线
  });

  // ========== 网络定义 ==========
  const nets: Omit<Net, 'id'>[] = [];

  // VCC 网络
  nets.push({
    name: 'VCC',
    pins: ['vcc-p1', 'ic1-p8', 'ic1-p4'],
    wires: [],
  });

  // GND 网络
  nets.push({
    name: 'GND',
    pins: ['ic1-p1', 'gnd-p1', 'led1-p2'],
    wires: [],
  });

  // OUTPUT 网络
  nets.push({
    name: 'OUTPUT',
    pins: ['ic1-p3', 'r3-p1'],
    wires: [],
  });

  // TIMING 网络
  nets.push({
    name: 'TIMING',
    pins: ['r1-p1', 'r1-p2', 'ic1-p7', 'ic1-p2', 'ic1-p6'],
    wires: [],
  });

  // CAP 网络
  nets.push({
    name: 'CAP',
    pins: ['r2-p2', 'c1-p1'],
    wires: [],
  });

  return { components, wires, nets };
}

// 保持向后兼容
export function createLEDFlashingCircuit() {
  return createLEDFlashingCircuitSimple();
}

export default createLEDFlashingCircuit;
