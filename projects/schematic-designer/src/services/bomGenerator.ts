import { Component, BOMItem, ProjectState } from '../types';

/**
 * BOM (Bill of Materials) 生成服务
 */
export class BOMGenerator {
  private project: ProjectState;

  constructor(project: ProjectState) {
    this.project = project;
  }

  /**
   * 生成 BOM 列表
   */
  generate(): BOMItem[] {
    const bomMap = new Map<string, BOMItem>();

    for (const comp of this.project.components) {
      const key = `${comp.type}:${comp.value}`;

      if (bomMap.has(key)) {
        // 累加数量
        const existing = bomMap.get(key)!;
        existing.quantity += 1;
        existing.reference += `, ${comp.reference}`;
      } else {
        // 新增条目
        bomMap.set(key, {
          reference: comp.reference,
          type: this.getComponentTypeName(comp.type),
          value: comp.value,
          quantity: 1,
          footprint: this.guessFootprint(comp),
          description: this.getDescription(comp),
        });
      }
    }

    return Array.from(bomMap.values()).sort((a, b) => {
      // 按类型分组，再按数量排序
      if (a.type !== b.type) return a.type.localeCompare(b.type);
      return b.quantity - a.quantity;
    });
  }

  /**
   * 导出 CSV 格式
   */
  toCSV(): string {
    const bom = this.generate();
    const headers = ['编号', '类型', '参数值', '数量', '封装', '描述'];

    const rows = bom.map((item, index) => [
      index + 1,
      item.type,
      item.value,
      item.quantity,
      item.footprint || '',
      item.description || '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    return csvContent;
  }

  /**
   * 导出 Markdown 格式
   */
  toMarkdown(): string {
    const bom = this.generate();

    let md = '# 物料清单 (BOM)\n\n';
    md += `**项目名称**: ${this.project.name}\n`;
    md += `**生成时间**: ${new Date().toLocaleString()}\n`;
    md += `**器件总数**: ${this.project.components.length}\n`;
    md += `**物料种类**: ${bom.length}\n\n`;

    md += '| 编号 | 类型 | 参数值 | 数量 | 封装 | 描述 |\n';
    md += '|------|------|--------|------|------|------|\n';

    bom.forEach((item, index) => {
      md += `| ${index + 1} | ${item.type} | ${item.value} | ${item.quantity} | ${item.footprint || '-'} | ${item.description || '-'} |\n`;
    });

    md += '\n---\n\n';
    md += '*由 Schematic Designer 自动生成*\n';

    return md;
  }

  /**
   * 导出 Excel 兼容的 TSV 格式
   */
  toTSV(): string {
    const bom = this.generate();
    const headers = ['编号', '类型', '参数值', '数量', '封装', '制造商', '料号', '描述'];

    const rows = bom.map((item, index) => [
      index + 1,
      item.type,
      item.value,
      item.quantity,
      item.footprint || '',
      item.manufacturer || '',
      item.partNumber || '',
      item.description || '',
    ]);

    const tsvContent = [
      headers.join('\t'),
      ...rows.map(row => row.join('\t')),
    ].join('\n');

    return tsvContent;
  }

  // ==================== 辅助方法 ====================

  private getComponentTypeName(type: string): string {
    const typeMap: Record<string, string> = {
      'R': '电阻',
      'C': '电容',
      'L': '电感',
      'D': '二极管',
      'LED': '发光二极管',
      'Q_NPN': 'NPN三极管',
      'Q_PNP': 'PNP三极管',
      'Q_NMOS': 'N沟道MOSFET',
      'Q_PMOS': 'P沟道MOSFET',
      'U_OPAMP': '运算放大器',
      'V': '电压源',
      'I': '电流源',
      'GND': '地',
      'J': '连接器',
      'U': '集成电路',
      'PWR': '电源符号',
    };

    return typeMap[type] || type;
  }

  private guessFootprint(comp: Component): string {
    // 根据器件类型猜测封装
    const footprintMap: Record<string, string> = {
      'R': '0805',
      'C': '0805',
      'L': '1210',
      'D': 'SOD-123',
      'LED': '0805',
      'Q_NPN': 'SOT-23',
      'Q_PNP': 'SOT-23',
      'Q_NMOS': 'SOT-23',
      'Q_PMOS': 'SOT-23',
      'U_OPAMP': 'DIP-8',
      'J': 'Pin Header 2.54mm',
    };

    return footprintMap[comp.type] || 'Unknown';
  }

  private getDescription(comp: Component): string {
    const descriptions: Record<string, string> = {
      'R': '碳膜/金属膜电阻',
      'C': '陶瓷/电解电容',
      'L': '贴片电感',
      'D': '整流/肖特基二极管',
      'LED': '发光二极管',
      'Q_NPN': 'NPN型三极管',
      'Q_PNP': 'PNP型三极管',
      'Q_NMOS': 'N沟道增强型MOSFET',
      'Q_PMOS': 'P沟道增强型MOSFET',
      'U_OPAMP': '通用运算放大器',
      'V': '直流电压源',
      'I': '直流电流源',
      'GND': '信号地',
      'J': '连接器',
      'U': '集成电路芯片',
      'PWR': '电源符号',
    };

    return descriptions[comp.type] || '';
  }
}

/**
 * 生成 BOM
 */
export function generateBOM(project: ProjectState): BOMItem[] {
  const generator = new BOMGenerator(project);
  return generator.generate();
}

/**
 * 导出 BOM 为不同格式
 */
export function exportBOM(project: ProjectState, format: 'csv' | 'md' | 'tsv'): string {
  const generator = new BOMGenerator(project);

  switch (format) {
    case 'csv':
      return generator.toCSV();
    case 'md':
      return generator.toMarkdown();
    case 'tsv':
      return generator.toTSV();
    default:
      return generator.toMarkdown();
  }
}
