import { ProjectState, RuleViolation, Component, Net, ComponentType } from '../types';
import { v4 as uuidv4 } from 'uuid';

// 器件额定电压/电流 (常见值)
const ComponentRatings: Record<ComponentType, { voltage?: number; current?: number; power?: number }> = {
  [ComponentType.RESISTOR]: { voltage: 200, current: 0.5, power: 0.25 }, // 常见 1/4W 电阻
  [ComponentType.CAPACITOR]: { voltage: 50 }, // 默认 50V 电容
  [ComponentType.INDUCTOR]: { current: 1 },
  [ComponentType.DIODE]: { current: 1, voltage: 1000 }, // 1A, 1000V
  [ComponentType.LED]: { current: 0.02, voltage: 5 }, // 20mA
  [ComponentType.NPN_TRANSISTOR]: { current: 0.5, voltage: 40 },
  [ComponentType.PNP_TRANSISTOR]: { current: 0.5, voltage: 40 },
  [ComponentType.NMOS]: { current: 5, voltage: 30 },
  [ComponentType.PMOS]: { current: 5, voltage: 30 },
  [ComponentType.OPAMP]: { voltage: 36 },
  [ComponentType.VOLTAGE_SOURCE]: { voltage: 30 },
  [ComponentType.CURRENT_SOURCE]: { current: 1 },
  [ComponentType.GND]: {},
  [ComponentType.CONNECTOR]: { voltage: 250 },
  [ComponentType.GENERIC_IC]: {},
  [ComponentType.POWER]: {},
};

/**
 * 设计规则检查服务
 * 检查原理图的电气规则是否符合要求
 */
export class DesignRuleChecker {
  private project: ProjectState;
  private violations: RuleViolation[] = [];

  constructor(project: ProjectState) {
    this.project = project;
  }

  /**
   * 执行所有规则检查
   */
  checkAll(): RuleViolation[] {
    this.violations = [];

    this.checkFloatingPins();           // 悬空引脚检查
    this.checkShortCircuits();          // 短路检查
    this.checkOpenNets();               // 开路检查
    this.checkPowerConnections();       // 电源连接检查
    this.checkVoltageRatings();         // 电压等级检查
    this.checkComponentRatings();       // 器件额定值检查
    this.checkDuplicateNets();          // 重复网络检查
    this.checkGroundConnections();      // 地连接检查

    return this.violations;
  }

  /**
   * 1. 检查悬空引脚 - 输入引脚不能悬空
   */
  private checkFloatingPins(): void {
    const components = this.project.components;

    for (const comp of components) {
      for (const pin of comp.pins) {
        // 输入引脚必须连接
        if (pin.direction === 'in' && !pin.connectedNet) {
          this.violations.push({
            id: uuidv4(),
            severity: 'error',
            rule: 'FLOATING_PIN',
            message: `器件 ${comp.reference} 的引脚 ${pin.name} (${pin.number}) 悬空 - 输入引脚必须连接`,
            elementId: comp.id,
            location: { x: comp.x, y: comp.y },
          });
        }
      }
    }
  }

  /**
   * 2. 检查短路 - 电源和地不能直接相连（除了通过电阻/电感）
   */
  private checkShortCircuits(): void {
    const nets = this.project.nets;

    for (const net of nets) {
      const connectedPins = this.getPinsInNet(net);

      // 检查是否有电源引脚和地引脚在同一个网络
      const hasPower = connectedPins.some(p => p.pin.direction === 'power' && p.comp.type === ComponentType.POWER);
      const hasGnd = connectedPins.some(p => p.comp.type === ComponentType.GND);

      if (hasPower && hasGnd) {
        // 检查中间是否有电阻等限流器件
        const componentsInNet = connectedPins.map(p => p.comp);

        // 如果只有电源、地和导线，直接报错
        const hasLimitComponent = componentsInNet.some(c =>
          [ComponentType.RESISTOR, ComponentType.INDUCTOR].includes(c.type)
        );

        if (!hasLimitComponent) {
          this.violations.push({
            id: uuidv4(),
            severity: 'error',
            rule: 'SHORT_CIRCUIT',
            message: `网络 ${net.name} 存在短路风险 - 电源和地直接相连`,
            elementId: net.id,
          });
        }
      }
    }
  }

  /**
   * 3. 检查开路 - 检查网络是否有不完整的连接
   */
  private checkOpenNets(): void {
    const nets = this.project.nets;

    for (const net of nets) {
      if (net.pins.length === 1) {
        this.violations.push({
          id: uuidv4(),
          severity: 'warning',
          rule: 'OPEN_NET',
          message: `网络 ${net.name || '未命名'} 只有 1 个引脚连接 - 可能存在开路`,
          elementId: net.id,
        });
      }

      // 检查网络是否有导线但引脚数少于2
      if (net.wires.length > 0 && net.pins.length < 2) {
        this.violations.push({
          id: uuidv4(),
          severity: 'warning',
          rule: 'ORPHAN_WIRE',
          message: `网络 ${net.name || '未命名'} 存在孤立的导线`,
          elementId: net.id,
        });
      }
    }
  }

  /**
   * 4. 检查电源连接 - 确保电源引脚正确连接
   */
  private checkPowerConnections(): void {
    const components = this.project.components;

    for (const comp of components) {
      const powerPins = comp.pins.filter(p => p.direction === 'power' && p.name !== 'GND');

      for (const pin of powerPins) {
        if (!pin.connectedNet) {
          this.violations.push({
            id: uuidv4(),
            severity: 'error',
            rule: 'MISSING_POWER',
            message: `器件 ${comp.reference} 的电源引脚 ${pin.name} 未连接`,
            elementId: comp.id,
            location: { x: comp.x, y: comp.y },
          });
        }
      }
    }
  }

  /**
   * 5. 检查电压等级 - 确保器件耐压足够
   */
  private checkVoltageRatings(): void {
    const voltageSources = this.project.components.filter(c => c.type === ComponentType.VOLTAGE_SOURCE);

    for (const vs of voltageSources) {
      const voltage = this.parseVoltage(vs.value);

      for (const comp of this.project.components) {
        const rating = ComponentRatings[comp.type];

        if (rating && rating.voltage && voltage > rating.voltage) {
          // 检查是否连接到同一网络
          const compPins = comp.pins.filter(p => p.connectedNet);
          const vsPins = vs.pins.filter(p => p.connectedNet);

          for (const cp of compPins) {
            for (const vp of vsPins) {
              if (cp.connectedNet === vp.connectedNet) {
                const safetyFactor = 1.5;
                if (voltage * safetyFactor > rating.voltage!) {
                  this.violations.push({
                    id: uuidv4(),
                    severity: 'error',
                    rule: 'VOLTAGE_OVERRATE',
                    message: `器件 ${comp.reference} 额定电压 ${rating.voltage}V 低于实际电压 ${voltage}V (×1.5 安全系数)`,
                    elementId: comp.id,
                    location: { x: comp.x, y: comp.y },
                  });
                }
              }
            }
          }
        }
      }
    }
  }

  /**
   * 6. 检查器件额定值 - 功率、电流等
   */
  private checkComponentRatings(): void {
    const nets = this.project.nets;

    for (const net of nets) {
      const connectedComponents = this.getComponentsInNet(net);

      // 检查电阻功率
      for (const comp of connectedComponents) {
        if (comp.type === ComponentType.RESISTOR) {
          const rating = ComponentRatings[ComponentType.RESISTOR];
          // resistance 可用于更精确的功率计算
          this.parseResistance(comp.value);

          // 计算电阻上的电压 (需要知道网络电压)
          // 这里简化处理，假设通过电流计算
          const currentSources = connectedComponents.filter(c => c.type === ComponentType.CURRENT_SOURCE);
          const voltageSources = connectedComponents.filter(c => c.type === ComponentType.VOLTAGE_SOURCE);

          if (voltageSources.length > 0 && currentSources.length > 0) {
            const voltage = this.parseVoltage(voltageSources[0].value);
            const current = this.parseCurrent(currentSources[0].value);
            const power = voltage * current;

            if (power > rating.power! * 0.8) {
              this.violations.push({
                id: uuidv4(),
                severity: 'warning',
                rule: 'POWER_OVERRATE',
                message: `电阻 ${comp.reference} 功率 ${power.toFixed(3)}W 超过额定功率 ${rating.power}W 的 80%`,
                elementId: comp.id,
                location: { x: comp.x, y: comp.y },
              });
            }
          }
        }
      }
    }
  }

  /**
   * 7. 检查重复网络名称
   */
  private checkDuplicateNets(): void {
    const nets = this.project.nets;
    const netNames = nets.map(n => n.name).filter(n => n);

    const duplicates = netNames.filter((name, index) =>
      netNames.indexOf(name) !== index
    );

    for (const name of duplicates) {
      this.violations.push({
        id: uuidv4(),
        severity: 'error',
        rule: 'DUPLICATE_NET',
        message: `网络名称 "${name}" 重复使用`,
      });
    }
  }

  /**
   * 8. 检查地连接 - 确保有地符号
   */
  private checkGroundConnections(): void {
    const hasGnd = this.project.components.some(c => c.type === ComponentType.GND);
    const hasPower = this.project.components.some(c => c.type === ComponentType.POWER || c.type === ComponentType.VOLTAGE_SOURCE);

    if (hasPower && !hasGnd) {
      this.violations.push({
        id: uuidv4(),
        severity: 'warning',
        rule: 'NO_GROUND',
        message: '电路中有电源但没有地符号 - 建议添加地连接',
      });
    }
  }

  // ==================== 辅助方法 ====================

  private getPinsInNet(net: Net): { comp: Component; pin: Component['pins'][0] }[] {
    const result: { comp: Component; pin: Component['pins'][0] }[] = [];

    for (const comp of this.project.components) {
      for (const pin of comp.pins) {
        if (net.pins.some((p: string) => p === `${comp.id}:${pin.id}`)) {
          result.push({ comp, pin });
        }
      }
    }

    return result;
  }

  private getComponentsInNet(net: Net): Component[] {
    const pinIds = new Set(net.pins);
    return this.project.components.filter(comp =>
      comp.pins.some(pin => pinIds.has(`${comp.id}:${pin.id}`))
    );
  }

  private parseVoltage(value: string): number {
    const match = value.match(/(\d+\.?\d*)\s*(V|mV|kV)?/i);
    if (!match) return 0;

    const num = parseFloat(match[1]);
    const unit = (match[2] || 'V').toUpperCase();

    switch (unit) {
      case 'MV': return num / 1000;
      case 'KV': return num * 1000;
      default: return num;
    }
  }

  private parseResistance(value: string): number {
    const match = value.match(/(\d+\.?\d*)\s*(Ω|MΩ|kΩ|Ω)?/i);
    if (!match) return 0;

    const num = parseFloat(match[1]);
    const unit = (match[2] || 'Ω').toUpperCase();

    switch (unit) {
      case 'MΩ': return num * 1000000;
      case 'KΩ': return num * 1000;
      default: return num;
    }
  }

  private parseCurrent(value: string): number {
    const match = value.match(/(\d+\.?\d*)\s*(A|mA|uA|nA)?/i);
    if (!match) return 0;

    const num = parseFloat(match[1]);
    const unit = (match[2] || 'A').toUpperCase();

    switch (unit) {
      case 'MA': return num / 1000;
      case 'UA': return num / 1000000;
      case 'NA': return num / 1000000000;
      default: return num;
    }
  }
}

/**
 * 执行设计规则检查
 */
export function checkDesignRules(project: ProjectState): RuleViolation[] {
  const checker = new DesignRuleChecker(project);
  return checker.checkAll();
}
