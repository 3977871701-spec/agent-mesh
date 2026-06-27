import { Net, Wire, Component } from '../types';

/**
 * 网络服务
 * 负责网络的创建、管理、命名和高亮
 */

// ==================== 网络创建 ====================

/**
 * 创建新网络
 */
export function createNet(name: string, pins: string[], wires: Wire[] = []): Omit<Net, 'id'> {
  return { name, pins, wires };
}

/**
 * 推断网络名称
 * 根据连接的器件引脚推断网络用途
 */
export function inferNetName(pins: { comp: Component; pinName: string }[]): string {
  let hasVCC = false;
  let hasGND = false;
  let hasOutput = false;
  let hasInput = false;

  for (const { comp, pinName } of pins) {
    const lowerName = pinName.toLowerCase();
    const lowerType = comp.type.toLowerCase();

    // 电源网络检测
    if (lowerName.includes('vcc') || lowerName.includes('vdd') || lowerName.includes('power')) {
      hasVCC = true;
    }
    if (lowerName.includes('gnd') || lowerName.includes('ground') || lowerName.includes('vss')) {
      hasGND = true;
    }

    // 器件类型检测
    if (lowerType.includes('gnd')) {
      hasGND = true;
    }
    if (lowerType.includes('power') || lowerType.includes('voltage')) {
      hasVCC = true;
    }
    if (lowerType.includes('led')) {
      hasOutput = true;
    }

    // 引脚名称检测
    if (lowerName.includes('out') || lowerName.includes('output')) {
      hasOutput = true;
    }
    if (lowerName.includes('in') || lowerName.includes('input') || lowerName.includes('trig') || lowerName.includes('thres')) {
      hasInput = true;
    }
  }

  // 返回优先级：GND > VCC > OUTPUT > 其他
  if (hasGND) return 'GND';
  if (hasVCC) return 'VCC';
  if (hasOutput) return 'OUTPUT';
  if (hasInput) return 'INPUT';

  return '';
}

// ==================== 网络查找 ====================

/**
 * 查找包含指定引脚的网络
 */
export function findNetByPin(netList: Net[], pinId: string): Net | null {
  return netList.find((net) => net.pins.includes(pinId)) || null;
}

/**
 * 查找包含指定导线的网络
 */
export function findNetByWire(netList: Net[], wireId: string): Net | null {
  return netList.find((net) => net.wires.some((w) => w.id === wireId)) || null;
}

/**
 * 获取网络的所有引脚信息
 */
export function getNetPinDetails(
  net: Net,
  components: Component[]
): { component: Component; pin: Component['pins'][0] }[] {
  const result: { component: Component; pin: Component['pins'][0] }[] = [];

  for (const pinId of net.pins) {
    const [compId, localPinId] = pinId.split(':');
    const comp = components.find((c) => c.id === compId);
    if (!comp) continue;

    const pin = comp.pins.find((p) => p.id === localPinId);
    if (pin) {
      result.push({ component: comp, pin });
    }
  }

  return result;
}

// ==================== 网络合并 ====================

/**
 * 合并两个网络
 */
export function mergeNets(net1: Net, net2: Net): Omit<Net, 'id'> {
  // 合并引脚 (去重)
  const allPins = [...new Set([...net1.pins, ...net2.pins])];
  // 合并导线 (去重)
  const allWires = [...net1.wires, ...net2.wires];
  // 优先使用已有的名称
  const name = net1.name || net2.name;

  return { name, pins: allPins, wires: allWires };
}

/**
 * 将引脚添加到网络
 */
export function addPinToNet(net: Net, pinId: string): Omit<Net, 'id'> {
  if (net.pins.includes(pinId)) {
    return { name: net.name, pins: net.pins, wires: net.wires };
  }
  return { name: net.name, pins: [...net.pins, pinId], wires: net.wires };
}

/**
 * 将导线添加到网络
 */
export function addWireToNet(net: Net, wire: Wire): Omit<Net, 'id'> {
  if (net.wires.some((w) => w.id === wire.id)) {
    return { name: net.name, pins: net.pins, wires: net.wires };
  }
  return { name: net.name, pins: net.pins, wires: [...net.wires, wire] };
}

// ==================== 网络高亮 ====================

/**
 * 获取网络高亮颜色
 * 根据网络名称返回对应颜色
 */
export function getNetHighlightColor(netName: string): string {
  const lowerName = netName.toLowerCase();

  if (lowerName === 'vcc' || lowerName === 'power' || lowerName === 'vdd') {
    return '#ff4444'; // 红色 - 电源
  }
  if (lowerName === 'gnd' || lowerName === 'ground' || lowerName === 'vss') {
    return '#44ff44'; // 绿色 - 地
  }

  // 其他网络使用蓝色系
  const hash = lowerName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const hue = (hash * 37) % 360;
  return `hsl(${hue}, 70%, 60%)`;
}

// ==================== 网络连通性验证 ====================

/**
 * 检查引脚是否连通
 */
export function arePinsConnected(
  pinId1: string,
  pinId2: string,
  nets: Net[]
): boolean {
  for (const net of nets) {
    if (net.pins.includes(pinId1) && net.pins.includes(pinId2)) {
      return true;
    }
  }
  return false;
}

/**
 * 获取两个引脚之间的连通路径
 */
export function findConnectionPath(
  startPinId: string,
  endPinId: string,
  nets: Net[]
): { net: Net } | null {
  for (const net of nets) {
    if (net.pins.includes(startPinId) && net.pins.includes(endPinId)) {
      return { net };
    }
  }
  return null;
}

/**
 * 检查网络是否完整 (至少2个引脚)
 */
export function isNetComplete(net: Net): boolean {
  return net.pins.length >= 2;
}

// ==================== 网络分组 ====================

/**
 * 按导线连通性分组网络
 */
export function groupWiresByConnectivity(
  wires: Wire[],
  nets: Net[]
): Wire[][] {
  const result: Wire[][] = [];
  const assigned = new Set<string>();

  for (const wire of wires) {
    if (assigned.has(wire.id)) continue;

    const group: Wire[] = [];
    const queue = [wire];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (assigned.has(current.id)) continue;

      assigned.add(current.id);
      group.push(current);

      // 查找通过引脚连通的其他导线
      for (const other of wires) {
        if (!assigned.has(other.id) && wiresSharePin(current, other, nets)) {
          queue.push(other);
        }
      }
    }

    if (group.length > 0) {
      result.push(group);
    }
  }

  return result;
}

function wiresSharePin(wire1: Wire, wire2: Wire, nets: Net[]): boolean {
  for (const net of nets) {
    if (net.wires.some((w) => w.id === wire1.id) && net.wires.some((w) => w.id === wire2.id)) {
      return true;
    }
  }
  return false;
}
