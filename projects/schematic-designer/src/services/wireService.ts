import { Wire, Component, Pin } from '../types';

/**
 * 导线绘制服务
 * 负责导线的创建、折线绘制、引脚连接等功能
 */

// ==================== 工具函数 ====================

/**
 * 计算两点之间的距离
 */
export function distance(x1: number, y1: number, x2: number, y2: number): number {
  return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
}

/**
 * 计算引脚的绝对坐标
 */
export function getPinAbsolutePosition(component: Component, pin: Pin): { x: number; y: number } {
  const rad = (component.rotation * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);

  // 旋转引脚位置
  const rotatedX = pin.x * cos - pin.y * sin;
  const rotatedY = pin.x * sin + pin.y * cos;

  return {
    x: component.x + rotatedX,
    y: component.y + rotatedY,
  };
}

/**
 * 查找最近的引脚
 */
export function findNearestPin(
  x: number,
  y: number,
  components: Component[],
  excludePinId?: string,
  maxDistance: number = 15
): { component: Component; pin: Pin; pinId: string } | null {
  let nearest: { component: Component; pin: Pin; pinId: string; dist: number } | null = null;

  for (const comp of components) {
    for (const pin of comp.pins) {
      const pinId = `${comp.id}:${pin.id}`;
      if (pinId === excludePinId) continue;

      const pos = getPinAbsolutePosition(comp, pin);
      const dist = distance(x, y, pos.x, pos.y);

      if (dist <= maxDistance && (!nearest || dist < nearest.dist)) {
        nearest = { component: comp, pin, pinId, dist };
      }
    }
  }

  return nearest ? { component: nearest.component, pin: nearest.pin, pinId: nearest.pinId } : null;
}

/**
 * 检查线段是否与引脚相交
 */
export function isPointNearPin(
  x: number,
  y: number,
  component: Component,
  pin: Pin,
  threshold: number = 10
): boolean {
  const pos = getPinAbsolutePosition(component, pin);
  return distance(x, y, pos.x, pos.y) <= threshold;
}

// ==================== 导线创建 ====================

/**
 * 创建一条直线导线
 */
export function createWireSegment(
  startX: number,
  startY: number,
  endX: number,
  endY: number
): Omit<Wire, 'id'> {
  return {
    points: [startX, startY, endX, endY],
  };
}

/**
 * 从折点序列创建导线
 */
export function createPolylineWire(points: number[]): Omit<Wire, 'id'> {
  return { points };
}

// ==================== 导线预览 ====================

/**
 * 生成导线预览路径 (SVG path)
 */
export function generateWirePreviewPath(
  waypoints: number[],
  currentX: number,
  currentY: number
): string {
  if (waypoints.length < 2) {
    return `M ${waypoints[0] || 0} ${waypoints[1] || 0} L ${currentX} ${currentY}`;
  }

  let path = `M ${waypoints[0]} ${waypoints[1]}`;
  for (let i = 2; i < waypoints.length; i += 2) {
    path += ` L ${waypoints[i]} ${waypoints[i + 1]}`;
  }
  path += ` L ${currentX} ${currentY}`;
  return path;
}

/**
 * 生成已完成导线的 SVG path
 */
export function generateWirePath(wire: Wire): string {
  const { points } = wire;
  if (points.length < 4 || points.length % 2 !== 0) {
    console.warn('[wireService] Invalid wire points:', points, 'length:', points.length);
    return '';
  }

  let path = `M ${points[0]} ${points[1]}`;
  for (let i = 2; i < points.length; i += 2) {
    path += ` L ${points[i]} ${points[i + 1]}`;
  }
  return path;
}

// ==================== 导线合并 ====================

/**
 * 合并相邻的共线导线段
 * 将起点/终点重合的多段导线合并为一段
 */
export function mergeAdjacentWires(wires: Wire[]): Wire[] {
  if (wires.length <= 1) return wires;

  const result: Wire[] = [];
  const processed = new Set<string>();

  for (const wire of wires) {
    if (processed.has(wire.id)) continue;

    // 尝试与其他导线合并
    let mergedPoints = [...wire.points];
    processed.add(wire.id);
    let merged = true;

    while (merged) {
      merged = false;
      for (const other of wires) {
        if (processed.has(other.id)) continue;

        // 检查是否可以直接合并
        const canMerge = checkWireCanMerge(mergedPoints, other.points);
        if (canMerge.canMerge) {
          mergedPoints = mergeWirePoints(mergedPoints, other.points, canMerge.mergeType);
          processed.add(other.id);
          merged = true;
        }
      }
    }

    result.push({ id: wire.id, points: mergedPoints });
  }

  return result;
}

function checkWireCanMerge(
  points1: number[],
  points2: number[]
): { canMerge: boolean; mergeType: 'start-start' | 'start-end' | 'end-start' | 'end-end' } {
  // points1 的起点
  const p1s = { x: points1[0], y: points1[1] };
  // points1 的终点
  const p1e = { x: points1[points1.length - 2], y: points1[points1.length - 1] };
  // points2 的起点
  const p2s = { x: points2[0], y: points2[1] };
  // points2 的终点
  const p2e = { x: points2[points2.length - 2], y: points2[points2.length - 1] };

  const threshold = 2;

  if (Math.abs(p1s.x - p2s.x) < threshold && Math.abs(p1s.y - p2s.y) < threshold) {
    return { canMerge: true, mergeType: 'start-start' };
  }
  if (Math.abs(p1s.x - p2e.x) < threshold && Math.abs(p1s.y - p2e.y) < threshold) {
    return { canMerge: true, mergeType: 'start-end' };
  }
  if (Math.abs(p1e.x - p2s.x) < threshold && Math.abs(p1e.y - p2s.y) < threshold) {
    return { canMerge: true, mergeType: 'end-start' };
  }
  if (Math.abs(p1e.x - p2e.x) < threshold && Math.abs(p1e.y - p2e.y) < threshold) {
    return { canMerge: true, mergeType: 'end-end' };
  }

  return { canMerge: false, mergeType: 'start-start' };
}

function mergeWirePoints(
  points1: number[],
  points2: number[],
  mergeType: 'start-start' | 'start-end' | 'end-start' | 'end-end'
): number[] {
  const p2Reversed = [...points2].reverse();

  switch (mergeType) {
    case 'start-start':
      return [...p2Reversed, ...points1.slice(2)];
    case 'start-end':
      return [...points2.slice(0, -2), ...points1];
    case 'end-start':
      return [...points1.slice(0, -2), ...points2];
    case 'end-end':
      return [...points1, ...p2Reversed.slice(2)];
    default:
      return points1;
  }
}

// ==================== 吸附到网格 ====================

/**
 * 吸附坐标到网格
 */
export function snapToGrid(value: number, gridSize: number, enabled: boolean): number {
  if (!enabled) return value;
  return Math.round(value / gridSize) * gridSize;
}

// ==================== 引脚碰撞检测 ====================

/**
 * 检测点是否在引脚附近
 */
export function isPointNearPinAtPosition(
  x: number,
  y: number,
  components: Component[],
  threshold: number = 12
): { component: Component; pin: Pin; pinId: string } | null {
  return findNearestPin(x, y, components, undefined, threshold);
}

// ==================== 导线交叉点检测 ====================

export interface Junction {
  x: number;
  y: number;
  wireIds: string[];
}

/**
 * 检测两条线段是否相交
 */
function lineSegmentsIntersect(
  x1: number, y1: number, x2: number, y2: number,
  x3: number, y3: number, x4: number, y4: number,
  threshold: number = 5
): { x: number; y: number } | null {
  // 使用向量叉积判断线段是否相交
  const epsilon = 0.0001;

  const d1x = x2 - x1;
  const d1y = y2 - y1;
  const d2x = x4 - x3;
  const d2y = y4 - y3;

  const cross = d1x * d2y - d1y * d2x;

  if (Math.abs(cross) < epsilon) {
    // 线段平行或共线
    return null;
  }

  const t = ((x3 - x1) * d2y - (y3 - y1) * d2x) / cross;
  const u = ((x3 - x1) * d1y - (y3 - y1) * d1x) / cross;

  // 检查 t 和 u 是否在 [0, 1] 范围内
  if (t >= -epsilon && t <= 1 + epsilon && u >= -epsilon && u <= 1 + epsilon) {
    const ix = x1 + t * d1x;
    const iy = y1 + t * d1y;

    // 检查是否在阈值范围内（考虑网格吸附）
    const dist1 = distance(x1, y1, ix, iy);
    const dist2 = distance(x2, y2, ix, iy);
    const dist3 = distance(x3, y3, ix, iy);
    const dist4 = distance(x4, y4, ix, iy);

    // 交点应该在两条线段的范围内
    if ((dist1 <= distance(x1, y1, x2, y2) + threshold) &&
        (dist2 <= distance(x1, y1, x2, y2) + threshold) &&
        (dist3 <= distance(x3, y3, x4, y4) + threshold) &&
        (dist4 <= distance(x3, y3, x4, y4) + threshold)) {
      return { x: ix, y: iy };
    }
  }

  return null;
}

/**
 * 获取折线的所有端点
 */
function getPolylineEndpoints(wire: Wire): { x: number; y: number }[] {
  const points: { x: number; y: number }[] = [];
  for (let i = 0; i < wire.points.length; i += 2) {
    points.push({ x: wire.points[i], y: wire.points[i + 1] });
  }
  return points;
}

/**
 * 获取折线的所有线段
 */
function getPolylineSegments(wire: Wire): { x1: number; y1: number; x2: number; y2: number }[] {
  const segments: { x1: number; y1: number; x2: number; y2: number }[] = [];
  const points = getPolylineEndpoints(wire);
  for (let i = 0; i < points.length - 1; i++) {
    segments.push({
      x1: points[i].x,
      y1: points[i].y,
      x2: points[i + 1].x,
      y2: points[i + 1].y,
    });
  }
  return segments;
}

/**
 * 检查点是否在阈值范围内
 */
function isPointNear(x: number, y: number, px: number, py: number, threshold: number): boolean {
  return Math.abs(x - px) <= threshold && Math.abs(y - py) <= threshold;
}

/**
 * 合并相近的结点
 */
function mergeNearbyJunctions(
  junctions: { x: number; y: number; wireIds: string[] }[],
  threshold: number = 5
): Junction[] {
  if (junctions.length === 0) return [];

  const merged: Junction[] = [];
  const used = new Set<number>();

  for (let i = 0; i < junctions.length; i++) {
    if (used.has(i)) continue;

    let current: Junction = {
      x: junctions[i].x,
      y: junctions[i].y,
      wireIds: [...junctions[i].wireIds],
    };

    for (let j = i + 1; j < junctions.length; j++) {
      if (used.has(j)) continue;

      if (isPointNear(junctions[i].x, junctions[i].y, junctions[j].x, junctions[j].y, threshold)) {
        current.wireIds = [...new Set([...current.wireIds, ...junctions[j].wireIds])];
        current.x = (current.x + junctions[j].x) / 2;
        current.y = (current.y + junctions[j].y) / 2;
        used.add(j);
      }
    }

    merged.push(current);
    used.add(i);
  }

  return merged;
}

/**
 * 查找导线交叉点（结点）
 * 返回所有导线相交的位置，这些位置需要绘制实心圆点表示电气连接
 */
export function findJunctions(wires: Wire[], threshold: number = 5): Junction[] {
  const junctions: { x: number; y: number; wireIds: string[] }[] = [];

  // 检查所有导线对的交叉
  for (let i = 0; i < wires.length; i++) {
    const wire1 = wires[i];
    const segments1 = getPolylineSegments(wire1);

    for (let j = i + 1; j < wires.length; j++) {
      const wire2 = wires[j];
      const segments2 = getPolylineSegments(wire2);

      // 检查所有线段对的交叉
      for (const seg1 of segments1) {
        for (const seg2 of segments2) {
          const intersection = lineSegmentsIntersect(
            seg1.x1, seg1.y1, seg1.x2, seg1.y2,
            seg2.x1, seg2.y1, seg2.x2, seg2.y2,
            threshold
          );

          if (intersection) {
            junctions.push({
              x: intersection.x,
              y: intersection.y,
              wireIds: [wire1.id, wire2.id],
            });
          }
        }
      }
    }
  }

  // 合并相近的结点
  return mergeNearbyJunctions(junctions, threshold);
}

/**
 * 查找特定位置的结点
 */
export function findJunctionAtPosition(
  x: number,
  y: number,
  junctions: Junction[],
  threshold: number = 5
): Junction | null {
  for (const junction of junctions) {
    if (isPointNear(x, y, junction.x, junction.y, threshold)) {
      return junction;
    }
  }
  return null;
}

/**
 * 检查结点是否需要显示
 * 只有当结点连接3条或以上导线时才显示（2条导线可以用T形连接表示）
 */
export function shouldShowJunction(junction: Junction): boolean {
  return junction.wireIds.length >= 3;
}
