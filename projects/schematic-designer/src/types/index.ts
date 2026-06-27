// 器件类型枚举
export enum ComponentType {
  RESISTOR = 'R',
  CAPACITOR = 'C',
  INDUCTOR = 'L',
  DIODE = 'D',
  LED = 'LED',
  NPN_TRANSISTOR = 'Q_NPN',
  PNP_TRANSISTOR = 'Q_PNP',
  NMOS = 'Q_NMOS',
  PMOS = 'Q_PMOS',
  OPAMP = 'U_OPAMP',
  VOLTAGE_SOURCE = 'V',
  CURRENT_SOURCE = 'I',
  GND = 'GND',
  CONNECTOR = 'J',
  GENERIC_IC = 'U',
  POWER = 'PWR',
}

// 器件数据接口
export interface Component {
  id: string;
  type: ComponentType;
  reference: string; // 如 R1, C2, U3
  value: string; // 如 10k, 100nF, LM358
  x: number;
  y: number;
  rotation: number; // 0, 90, 180, 270
  pins: Pin[];
  properties: Record<string, string>;
}

// 引脚接口
export interface Pin {
  id: string;
  name: string;
  number: string;
  x: number; // 相对位置
  y: number;
  direction: 'in' | 'out' | 'bidirectional' | 'power';
  connectedNet?: string;
}

// 网络接口
export interface Net {
  id: string;
  name: string;
  pins: string[]; // 连接的引脚 ID
  wires: Wire[];
}

// 导线接口 - 支持折线
export interface Wire {
  id: string;
  points: number[]; // [x1, y1, x2, y2, x3, y3, ...] 折点序列
}

// 导线绘制状态
export interface WireDrawingState {
  isDrawing: boolean;
  startPinId: string | null;       // 起始引脚 ID "compId:pinId"
  startX: number;
  startY: number;
  waypoints: number[];            // 当前折点 [x1, y1, x2, y2, ...]
  currentX: number;               // 鼠标当前位置
  currentY: number;
}

// 设计规则违规
export interface RuleViolation {
  id: string;
  severity: 'error' | 'warning';
  rule: string;
  message: string;
  elementId?: string;
  location?: { x: number; y: number };
}

// BOM 项目
export interface BOMItem {
  reference: string;
  type: string;
  value: string;
  quantity: number;
  footprint?: string;
  manufacturer?: string;
  partNumber?: string;
  description?: string;
}

// 项目状态
export interface ProjectState {
  name: string;
  components: Component[];
  nets: Net[];
  wires: Wire[];
  violations: RuleViolation[];
  selectedComponent?: string;
  gridSize: number;
  snapToGrid: boolean;
}

// 设计规则
export interface DesignRule {
  id: string;
  name: string;
  description: string;
  check: (project: ProjectState) => RuleViolation[];
}

// 导出格式
export type ExportFormat = 'dxf' | 'svg' | 'png' | 'pdf' | 'ad-json' | 'lceda-json';

// 原理图格式
export interface SchematicFormat {
  type: 'ad' | 'lceda';
  version: string;
  data: {
    components: Component[];
    nets: Net[];
    wires: Wire[];
  };
}
