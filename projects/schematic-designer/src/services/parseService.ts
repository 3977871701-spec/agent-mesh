import JSZip from 'jszip';
import { Component, Net, Wire, ProjectState, ComponentType } from '../types';
import { v4 as uuidv4 } from 'uuid';

/**
 * 原理图解析服务 - 支持导入 AD 和 LCEDA 格式
 */
export class ParseService {
  /**
   * 从 AD .SchDoc 压缩包格式解析 (Altium Designer)
   * .SchDoc 文件通常是包含多个文件的 ZIP 压缩包
   */
  async parseFromSchDoc(fileContent: ArrayBuffer): Promise<Partial<ProjectState>> {
    try {
      const zip = await JSZip.loadAsync(fileContent);
      const result: Partial<ProjectState> = {
        components: [],
        nets: [],
        wires: [],
      };

      // 查找并解析原理图 JSON 文件
      const files = zip.filter((_, file) => !file.dir);

      for (const file of files) {
        const filename = file.name.toLowerCase();

        // 查找原理图相关文件
        if (
          filename.endsWith('.sch.json') ||
          filename.endsWith('.sch') ||
          filename.includes('schematic')
        ) {
          const content = await file.async('string');

          try {
            const parsed = JSON.parse(content);

            // AD 格式
            if (parsed.type === 'schematic' || parsed.version) {
              const adResult = this.parseFromAD(content);
              result.components = [...(result.components || []), ...(adResult.components || [])];
              result.nets = [...(result.nets || []), ...(adResult.nets || [])];
              result.wires = [...(result.wires || []), ...(adResult.wires || [])];
            }
            // LCEDA 格式
            else if (parsed.docType === 'sch') {
              const lcedaResult = this.parseFromLCEDA(content);
              result.components = [...(result.components || []), ...(lcedaResult.components || [])];
              result.nets = [...(result.nets || []), ...(lcedaResult.nets || [])];
              result.wires = [...(result.wires || []), ...(lcedaResult.wires || [])];
            }
          } catch {
            // 如果单个文件解析失败，继续处理其他文件
            console.warn(`Failed to parse file: ${file.name}`);
          }
        }
      }

      // 如果没有找到特定格式，尝试将整个 ZIP 作为 JSON 解析
      if (result.components?.length === 0) {
        for (const file of files) {
          if (file.name.endsWith('.json')) {
            const content = await file.async('string');
            try {
              const parsed = JSON.parse(content);
              if (parsed.data?.components || parsed.components) {
                const adResult = this.parseFromAD(content);
                if (adResult.components?.length) {
                  result.components = adResult.components;
                  result.nets = adResult.nets;
                  result.wires = adResult.wires;
                  break;
                }
              }
            } catch {
              // continue
            }
          }
        }
      }

      return result;
    } catch (error) {
      throw new Error(`Failed to parse .SchDoc format: ${error}`);
    }
  }

  /**
   * 从 ArrayBuffer 解析文件（自动检测格式）
   */
  async parseFromArrayBuffer(buffer: ArrayBuffer, filename: string): Promise<Partial<ProjectState>> {
    const ext = filename.toLowerCase();

    // .SchDoc 是压缩包格式
    if (ext.endsWith('.schdoc') || ext.endsWith('.scharc')) {
      return this.parseFromSchDoc(buffer);
    }

    // 尝试作为纯 JSON 解析
    const decoder = new TextDecoder('utf-8');
    const content = decoder.decode(buffer);
    return this.parseFromFile(content, filename);
  }

  /**
   * 从 AD JSON 格式解析
   */
  parseFromAD(jsonString: string): Partial<ProjectState> {
    try {
      const format = JSON.parse(jsonString) as Record<string, unknown>;

      if (format.type !== 'ad' && !format.version) {
        throw new Error('Invalid AD format: wrong type');
      }

      const data = (format.data || format) as {
        components?: Component[];
        nets?: Net[];
        wires?: Wire[];
      };

      return {
        components: data.components || [],
        nets: data.nets || [],
        wires: data.wires || [],
      };
    } catch (error) {
      throw new Error(`Failed to parse AD format: ${error}`);
    }
  }

  /**
   * 从 LCEDA JSON 格式解析
   */
  parseFromLCEDA(jsonString: string): Partial<ProjectState> {
    try {
      const format = JSON.parse(jsonString);

      if (format.docType !== 'sch') {
        throw new Error('Invalid LCEDA format: wrong docType');
      }

      const components: Component[] = [];
      const nets: Net[] = [];

      // 转换 LCEDA components 到我们的格式
      if (format.data.components) {
        for (const lcComp of format.data.components) {
          const component: Component = {
            id: lcComp.id || uuidv4(),
            type: this.mapLCEDAComponentType(lcComp.type),
            reference: lcComp.name,
            value: lcComp.value || '',
            x: lcComp.x,
            y: lcComp.y,
            rotation: lcComp.rotation || 0,
            pins: (lcComp.pins || []).map((p: any) => ({
              id: p.id || uuidv4(),
              name: p.name,
              number: p.number || p.name,
              x: p.x - lcComp.x,
              y: p.y - lcComp.y,
              direction: 'bidirectional' as const,
            })),
            properties: {},
          };
          components.push(component);
        }
      }

      // 转换 LCEDA nets
      if (format.data.nets) {
        for (const lcNet of format.data.nets) {
          const net: Net = {
            id: uuidv4(),
            name: lcNet.name || '',
            pins: lcNet.pins || [],
            wires: [],
          };
          nets.push(net);
        }
      }

      // 转换导线
      const wires: Wire[] = [];
      if (format.data.paths) {
        for (const path of format.data.paths) {
          if (path.type === 'wire') {
            if (Array.isArray(path.points) && path.points.length >= 4) {
              wires.push({
                id: uuidv4(),
                points: path.points,
              });
            } else if (path.x1 !== undefined && path.y1 !== undefined && path.x2 !== undefined && path.y2 !== undefined) {
              // Legacy format support
              wires.push({
                id: uuidv4(),
                points: [path.x1, path.y1, path.x2, path.y2],
              });
            }
          }
        }
      }

      return { components, nets, wires };
    } catch (error) {
      throw new Error(`Failed to parse LCEDA format: ${error}`);
    }
  }

  /**
   * 从文件内容自动检测格式并解析
   */
  parseFromFile(content: string, filename: string): Partial<ProjectState> {
    const ext = filename.toLowerCase();

    if (ext.endsWith('.json')) {
      // 尝试检测是 AD 还是 LCEDA 格式
      try {
        const json = JSON.parse(content);

        if (json.type === 'schematic' || json.version) {
          return this.parseFromAD(content);
        } else if (json.docType === 'sch') {
          return this.parseFromLCEDA(content);
        }
      } catch {
        throw new Error('Invalid JSON format');
      }
    }

    throw new Error(`Unsupported file format: ${ext}`);
  }

  /**
   * 从自然语言描述解析并生成原理图
   */
  parseFromDescription(description: string): Partial<ProjectState> {
    const lowerDesc = description.toLowerCase();

    // 简单关键词匹配
    const components: Component[] = [];
    const nets: Net[] = [];

    // LED 闪烁电路示例
    if (lowerDesc.includes('led') && lowerDesc.includes('闪烁')) {
      // R1 - 限流电阻
      components.push(this.createComponent(ComponentType.RESISTOR, 'R1', '330', 100, 100));
      // LED1
      components.push(this.createComponent(ComponentType.LED, 'LED1', 'Red', 200, 100));
      // V1 - 电源
      components.push(this.createComponent(ComponentType.VOLTAGE_SOURCE, 'V1', '5V', 50, 100));
      // GND
      components.push(this.createComponent(ComponentType.GND, 'GND', '0V', 200, 200));

      // 网络
      nets.push({
        id: uuidv4(),
        name: 'VCC',
        pins: ['R1:1', 'V1:1'],
        wires: [],
      });
      nets.push({
        id: uuidv4(),
        name: 'GND',
        pins: ['LED1:2', 'GND:1'],
        wires: [],
      });
    }

    // 电压分压器
    if (lowerDesc.includes('分压') || lowerDesc.includes('voltage divider')) {
      components.push(this.createComponent(ComponentType.RESISTOR, 'R1', '10k', 100, 100));
      components.push(this.createComponent(ComponentType.RESISTOR, 'R2', '10k', 200, 100));
      components.push(this.createComponent(ComponentType.VOLTAGE_SOURCE, 'V1', '5V', 50, 100));
      components.push(this.createComponent(ComponentType.GND, 'GND', '0V', 250, 100));
    }

    // 经典运放放大电路
    if (lowerDesc.includes('运放') || lowerDesc.includes('opamp') || lowerDesc.includes('放大')) {
      components.push(this.createComponent(ComponentType.OPAMP, 'U1', 'LM358', 200, 150));
      components.push(this.createComponent(ComponentType.RESISTOR, 'R1', '10k', 100, 100));
      components.push(this.createComponent(ComponentType.RESISTOR, 'R2', '10k', 100, 200));
      components.push(this.createComponent(ComponentType.RESISTOR, 'R3', '10k', 300, 100));
      components.push(this.createComponent(ComponentType.RESISTOR, 'R4', '10k', 300, 200));
      components.push(this.createComponent(ComponentType.VOLTAGE_SOURCE, 'VCC', '12V', 50, 50));
      components.push(this.createComponent(ComponentType.VOLTAGE_SOURCE, 'VEE', '-12V', 50, 250));
      components.push(this.createComponent(ComponentType.GND, 'GND', '0V', 200, 250));
    }

    // 稳压电源
    if (lowerDesc.includes('稳压') || lowerDesc.includes('电源')) {
      components.push(this.createComponent(ComponentType.VOLTAGE_SOURCE, 'VIN', '12V', 50, 100));
      components.push(this.createComponent(ComponentType.CAPACITOR, 'C1', '100uF', 120, 100));
      components.push(this.createComponent(ComponentType.DIODE, 'D1', '1N4007', 180, 100));
      components.push(this.createComponent(ComponentType.CAPACITOR, 'C2', '100uF', 240, 100));
      components.push(this.createComponent(ComponentType.GND, 'GND', '0V', 200, 200));
    }

    return {
      name: this.extractProjectName(description),
      components,
      nets,
      wires: [],
    };
  }

  // ==================== 辅助方法 ====================

  private createComponent(
    type: ComponentType,
    reference: string,
    value: string,
    x: number,
    y: number
  ): Component {
    return {
      id: uuidv4(),
      type,
      reference,
      value,
      x,
      y,
      rotation: 0,
      pins: [],
      properties: {},
    };
  }

  private mapLCEDAComponentType(lcType: string): ComponentType {
    const typeMap: Record<string, ComponentType> = {
      'R': ComponentType.RESISTOR,
      'C': ComponentType.CAPACITOR,
      'L': ComponentType.INDUCTOR,
      'D': ComponentType.DIODE,
      'Q': ComponentType.NPN_TRANSISTOR,
      'U': ComponentType.GENERIC_IC,
      'J': ComponentType.CONNECTOR,
      'V': ComponentType.VOLTAGE_SOURCE,
    };

    return typeMap[lcType] || ComponentType.GENERIC_IC;
  }

  private extractProjectName(description: string): string {
    // 尝试从描述中提取项目名称
    const lines = description.split('\n');
    if (lines.length > 0 && lines[0].length < 50) {
      return lines[0].trim();
    }
    return '未命名项目';
  }
}

/**
 * 解析原理图文件
 */
export function parseSchematicFile(content: string, filename: string): Partial<ProjectState> {
  const service = new ParseService();
  return service.parseFromFile(content, filename);
}

/**
 * 从 ArrayBuffer 解析原理图文件（支持 .SchDoc 压缩包）
 */
export async function parseSchematicFileAsync(buffer: ArrayBuffer, filename: string): Promise<Partial<ProjectState>> {
  const service = new ParseService();
  return service.parseFromArrayBuffer(buffer, filename);
}

/**
 * 从描述生成原理图
 */
export function generateFromDescription(description: string): Partial<ProjectState> {
  const service = new ParseService();
  return service.parseFromDescription(description);
}
