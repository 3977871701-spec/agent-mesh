import React from 'react';
import { ComponentType } from '../../types';

// 器件符号 SVG 定义
export const ComponentSymbols: Record<ComponentType, React.FC<{ x: number; y: number; rotation?: number }>> = {
  [ComponentType.RESISTOR]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <path
        d="M -30,0 L -20,0 L -15,-8 L -5,8 L 5,-8 L 15,8 L 20,0 L 30,0"
        className="component-symbol"
      />
      <circle cx="0" cy="0" r="2" className="pin" />
      <circle cx="-30" cy="0" r="2" className="pin" />
      <circle cx="30" cy="0" r="2" className="pin" />
    </g>
  ),

  [ComponentType.CAPACITOR]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-30" y1="0" x2="-5" y2="0" className="component-symbol" />
      <line x1="-5" y1="-12" x2="-5" y2="12" className="component-symbol" />
      <line x1="5" y1="-12" x2="5" y2="12" className="component-symbol" />
      <line x1="5" y1="0" x2="30" y2="0" className="component-symbol" />
      <circle cx="0" cy="0" r="2" className="pin" />
      <circle cx="-30" cy="0" r="2" className="pin" />
      <circle cx="30" cy="0" r="2" className="pin" />
    </g>
  ),

  [ComponentType.INDUCTOR]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <path
        d="M -30,0 L -20,0 Q -15,0 -12,-6 Q -9,-12 -6,-6 Q -3,0 0,-6 Q 3,-12 6,-6 Q 9,0 12,-6 Q 15,-12 18,-6 Q 21,0 20,0 L 30,0"
        className="component-symbol"
      />
      <circle cx="-30" cy="0" r="2" className="pin" />
      <circle cx="30" cy="0" r="2" className="pin" />
    </g>
  ),

  [ComponentType.DIODE]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-30" y1="0" x2="-10" y2="0" className="component-symbol" />
      <polygon points="-10,-10 -10,10 10,0" className="component-symbol" fill="transparent" />
      <line x1="10" y1="-10" x2="10" y2="10" className="component-symbol" />
      <line x1="10" y1="0" x2="30" y2="0" className="component-symbol" />
      <circle cx="-30" cy="0" r="2" className="pin" />
      <circle cx="30" cy="0" r="2" className="pin" />
    </g>
  ),

  [ComponentType.LED]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-30" y1="0" x2="-10" y2="0" className="component-symbol" />
      <polygon points="-10,-10 -10,10 10,0" className="component-symbol" fill="transparent" />
      <line x1="10" y1="-10" x2="10" y2="10" className="component-symbol" />
      <line x1="10" y1="0" x2="30" y2="0" className="component-symbol" />
      {/* LED 箭头 */}
      <line x1="5" y1="-12" x2="15" y2="-18" className="component-symbol" />
      <line x1="10" y1="-20" x2="15" y2="-18" className="component-symbol" />
      <line x1="10" y1="-20" x2="5" y2="-12" className="component-symbol" />
      <circle cx="-30" cy="0" r="2" className="pin" />
      <circle cx="30" cy="0" r="2" className="pin" />
    </g>
  ),

  [ComponentType.NPN_TRANSISTOR]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-25" y1="0" x2="0" y2="0" className="component-symbol" />
      <line x1="0" y1="0" x2="15" y2="-15" className="component-symbol" />
      <line x1="0" y1="0" x2="15" y2="15" className="component-symbol" />
      <polygon points="10,-20 18,-12 12,-10" fill="#00ff88" />
      <line x1="15" y1="-15" x2="30" y2="-15" className="component-symbol" />
      <line x1="15" y1="15" x2="30" y2="15" className="component-symbol" />
      <circle cx="-25" cy="0" r="2" className="pin" />
      <circle cx="30" cy="-15" r="2" className="pin" />
      <circle cx="30" cy="15" r="2" className="pin" />
    </g>
  ),

  [ComponentType.PNP_TRANSISTOR]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-25" y1="0" x2="0" y2="0" className="component-symbol" />
      <line x1="0" y1="0" x2="15" y2="-15" className="component-symbol" />
      <line x1="0" y1="0" x2="15" y2="15" className="component-symbol" />
      <polygon points="5,-5 18,-12 12,-10" fill="#00ff88" />
      <line x1="15" y1="-15" x2="30" y2="-15" className="component-symbol" />
      <line x1="15" y1="15" x2="30" y2="15" className="component-symbol" />
      <circle cx="-25" cy="0" r="2" className="pin" />
      <circle cx="30" cy="-15" r="2" className="pin" />
      <circle cx="30" cy="15" r="2" className="pin" />
    </g>
  ),

  [ComponentType.NMOS]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-25" y1="0" x2="0" y2="0" className="component-symbol" />
      <line x1="0" y1="-15" x2="0" y2="15" className="component-symbol" />
      <line x1="0" y1="-15" x2="8" y2="-15" className="component-symbol" />
      <line x1="0" y1="0" x2="15" y2="-10" className="component-symbol" />
      <polygon points="10,-15 18,-7 12,-5" fill="#00ff88" />
      <line x1="15" y1="-10" x2="25" y2="-10" className="component-symbol" />
      <line x1="0" y1="15" x2="25" y2="15" className="component-symbol" />
      <circle cx="-25" cy="0" r="2" className="pin" />
      <circle cx="25" cy="-10" r="2" className="pin" />
      <circle cx="25" cy="15" r="2" className="pin" />
    </g>
  ),

  [ComponentType.PMOS]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <line x1="-25" y1="0" x2="0" y2="0" className="component-symbol" />
      <line x1="0" y1="-15" x2="0" y2="15" className="component-symbol" />
      <line x1="-5" y1="-15" x2="5" y2="-15" className="component-symbol" />
      <line x1="0" y1="0" x2="15" y2="-10" className="component-symbol" />
      <polygon points="5,-5 18,-12 12,-10" fill="#00ff88" />
      <line x1="15" y1="-10" x2="25" y2="-10" className="component-symbol" />
      <line x1="0" y1="15" x2="25" y2="15" className="component-symbol" />
      <circle cx="-25" cy="0" r="2" className="pin" />
      <circle cx="25" cy="-10" r="2" className="pin" />
      <circle cx="25" cy="15" r="2" className="pin" />
    </g>
  ),

  [ComponentType.OPAMP]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <polygon points="-20,-25 -20,25 20,0" className="component-symbol" fill="transparent" />
      <text x="-35" y="5" className="pin-label">-</text>
      <text x="-35" y="-15" className="pin-label">+</text>
      <text x="25" y="5" className="pin-label">OUT</text>
      <line x1="-40" y1="0" x2="-20" y2="0" className="component-symbol" />
      <line x1="-40" y1="-20" x2="-20" y2="-20" className="component-symbol" />
      <line x1="20" y1="0" x2="40" y2="0" className="component-symbol" />
      <line x1="-20" y1="25" x2="-20" y2="35" className="component-symbol" />
      <line x1="20" y1="25" x2="20" y2="35" className="component-symbol" />
      <circle cx="-40" cy="0" r="2" className="pin" />
      <circle cx="-40" cy="-20" r="2" className="pin" />
      <circle cx="40" cy="0" r="2" className="pin" />
      <circle cx="-20" cy="35" r="2" className="pin" />
      <circle cx="20" cy="35" r="2" className="pin" />
    </g>
  ),

  [ComponentType.VOLTAGE_SOURCE]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <circle cx="0" cy="0" r="20" className="component-symbol" />
      <line x1="0" y1="0" x2="0" y2="-8" className="component-symbol" />
      <line x1="-6" y1="-4" x2="6" y2="-4" className="component-symbol" />
      <line x1="-3" y1="0" x2="3" y2="0" className="component-symbol" />
      <line x1="0" y1="8" x2="0" y2="20" className="component-symbol" />
      <line x1="0" y1="-20" x2="0" y2="-30" className="component-symbol" />
      <text x="5" y="-30" className="net-label">+</text>
      <text x="5" y="30" className="net-label">-</text>
      <circle cx="0" cy="-30" r="2" className="pin" />
      <circle cx="0" cy="30" r="2" className="pin" />
    </g>
  ),

  [ComponentType.CURRENT_SOURCE]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <circle cx="0" cy="0" r="20" className="component-symbol" />
      <line x1="0" y1="20" x2="0" y2="8" className="component-symbol" />
      <line x1="0" y1="-20" x2="0" y2="-8" className="component-symbol" />
      <line x1="-7" y1="-8" x2="7" y2="-8" className="component-symbol" />
      <polygon points="0,-12 -5,-5 5,-5" fill="#00ff88" />
      <circle cx="0" cy="-30" r="2" className="pin" />
      <circle cx="0" cy="30" r="2" className="pin" />
    </g>
  ),

  [ComponentType.GND]: ({ x, y }) => (
    <g transform={`translate(${x}, ${y})`}>
      <line x1="0" y1="-10" x2="0" y2="0" className="component-symbol" />
      <line x1="-15" y1="0" x2="15" y2="0" className="component-symbol" />
      <line x1="-10" y1="5" x2="10" y2="5" className="component-symbol" />
      <line x1="-5" y1="10" x2="5" y2="10" className="component-symbol" />
      <circle cx="0" cy="-10" r="2" className="pin" />
    </g>
  ),

  [ComponentType.CONNECTOR]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <rect x="-20" y="-15" width="40" height="30" className="component-symbol" rx="3" />
      <circle cx="-12" cy="0" r="3" className="pin" />
      <circle cx="0" cy="0" r="3" className="pin" />
      <circle cx="12" cy="0" r="3" className="pin" />
    </g>
  ),

  [ComponentType.GENERIC_IC]: ({ x, y, rotation = 0 }) => (
    <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
      <rect x="-30" y="-40" width="60" height="80" className="component-symbol" rx="2" />
      {/* 引脚 */}
      {[-30, -10, 10, 30].map((py, i) => (
        <React.Fragment key={i}>
          <line x1="-30" y1={py} x2="-40" y2={py} className="component-symbol" />
          <circle cx="-40" cy={py} r="2" className="pin" />
        </React.Fragment>
      ))}
      {[-30, -10, 10, 30].map((py, i) => (
        <React.Fragment key={i + 4}>
          <line x1="30" y1={py} x2="40" y2={py} className="component-symbol" />
          <circle cx="40" cy={py} r="2" className="pin" />
        </React.Fragment>
      ))}
    </g>
  ),

  [ComponentType.POWER]: ({ x, y }) => (
    <g transform={`translate(${x}, ${y})`}>
      <line x1="0" y1="0" x2="0" y2="-15" className="component-symbol" />
      <polygon points="-8,-15 8,-15 0,-25" className="component-symbol" fill="#00ff88" />
      <circle cx="0" cy="0" r="2" className="pin" />
    </g>
  ),
};

// 获取器件默认引脚
export const DefaultPins: Record<ComponentType, { name: string; direction: 'in' | 'out' | 'bidirectional' | 'power' }[]> = {
  [ComponentType.RESISTOR]: [
    { name: '1', direction: 'bidirectional' },
    { name: '2', direction: 'bidirectional' },
  ],
  [ComponentType.CAPACITOR]: [
    { name: '1', direction: 'bidirectional' },
    { name: '2', direction: 'bidirectional' },
  ],
  [ComponentType.INDUCTOR]: [
    { name: '1', direction: 'bidirectional' },
    { name: '2', direction: 'bidirectional' },
  ],
  [ComponentType.DIODE]: [
    { name: 'A', direction: 'in' },
    { name: 'K', direction: 'out' },
  ],
  [ComponentType.LED]: [
    { name: 'A', direction: 'in' },
    { name: 'K', direction: 'out' },
  ],
  [ComponentType.NPN_TRANSISTOR]: [
    { name: 'B', direction: 'in' },
    { name: 'C', direction: 'out' },
    { name: 'E', direction: 'out' },
  ],
  [ComponentType.PNP_TRANSISTOR]: [
    { name: 'B', direction: 'in' },
    { name: 'C', direction: 'out' },
    { name: 'E', direction: 'out' },
  ],
  [ComponentType.NMOS]: [
    { name: 'G', direction: 'in' },
    { name: 'D', direction: 'out' },
    { name: 'S', direction: 'out' },
  ],
  [ComponentType.PMOS]: [
    { name: 'G', direction: 'in' },
    { name: 'D', direction: 'out' },
    { name: 'S', direction: 'out' },
  ],
  [ComponentType.OPAMP]: [
    { name: 'V+', direction: 'in' },
    { name: 'V-', direction: 'in' },
    { name: 'OUT', direction: 'out' },
    { name: 'VCC', direction: 'power' },
    { name: 'VEE', direction: 'power' },
  ],
  [ComponentType.VOLTAGE_SOURCE]: [
    { name: '+', direction: 'power' },
    { name: '-', direction: 'power' },
  ],
  [ComponentType.CURRENT_SOURCE]: [
    { name: '+', direction: 'power' },
    { name: '-', direction: 'power' },
  ],
  [ComponentType.GND]: [
    { name: 'GND', direction: 'power' },
  ],
  [ComponentType.CONNECTOR]: [
    { name: '1', direction: 'bidirectional' },
    { name: '2', direction: 'bidirectional' },
    { name: '3', direction: 'bidirectional' },
  ],
  [ComponentType.GENERIC_IC]: [
    { name: 'NC1', direction: 'bidirectional' },
    { name: 'NC2', direction: 'bidirectional' },
    { name: 'NC3', direction: 'bidirectional' },
    { name: 'NC4', direction: 'bidirectional' },
    { name: 'NC5', direction: 'bidirectional' },
    { name: 'NC6', direction: 'bidirectional' },
    { name: 'NC7', direction: 'bidirectional' },
    { name: 'NC8', direction: 'bidirectional' },
  ],
  [ComponentType.POWER]: [
    { name: 'VCC', direction: 'power' },
  ],
};

// 器件中文名称
export const ComponentNames: Record<ComponentType, string> = {
  [ComponentType.RESISTOR]: '电阻',
  [ComponentType.CAPACITOR]: '电容',
  [ComponentType.INDUCTOR]: '电感',
  [ComponentType.DIODE]: '二极管',
  [ComponentType.LED]: '发光二极管',
  [ComponentType.NPN_TRANSISTOR]: 'NPN 三极管',
  [ComponentType.PNP_TRANSISTOR]: 'PNP 三极管',
  [ComponentType.NMOS]: 'N 沟道 MOSFET',
  [ComponentType.PMOS]: 'P 沟道 MOSFET',
  [ComponentType.OPAMP]: '运算放大器',
  [ComponentType.VOLTAGE_SOURCE]: '电压源',
  [ComponentType.CURRENT_SOURCE]: '电流源',
  [ComponentType.GND]: '地',
  [ComponentType.CONNECTOR]: '连接器',
  [ComponentType.GENERIC_IC]: '通用 IC',
  [ComponentType.POWER]: '电源符号',
};
