import { ProjectState, SchematicFormat, Component, Wire } from '../types';
import { saveAs } from 'file-saver';

/**
 * 导出服务 - 支持多种格式
 */
export class ExportService {
  private project: ProjectState;

  constructor(project: ProjectState) {
    this.project = project;
  }

  /**
   * 导出为 Altium Designer JSON 格式
   */
  exportToAD(): Blob {
    const format: SchematicFormat = {
      type: 'ad',
      version: '1.0',
      data: {
        components: this.project.components,
        nets: this.project.nets,
        wires: this.project.wires,
      },
    };

    const json = JSON.stringify(format, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  /**
   * 导出为嘉立创 EDA JSON 格式
   */
  exportToLCEDA(): Blob {
    // 转换为 LCEDA 格式
    const lcedaFormat = {
      docType: 'sch',
      version: '1.0',
      data: {
        components: this.project.components.map(c => ({
          id: c.id,
          type: c.type,
          name: c.reference,
          value: c.value,
          x: c.x,
          y: c.y,
          rotation: c.rotation,
          pins: c.pins.map(p => ({
            id: p.id,
            name: p.name,
            number: p.number,
            x: c.x + p.x,
            y: c.y + p.y,
          })),
        })),
        paths: this.project.wires.map(w => ({
          type: 'wire',
          points: w.points,
        })),
        nets: this.project.nets.map(n => ({
          name: n.name,
          pins: n.pins,
        })),
      },
    };

    const json = JSON.stringify(lcedaFormat, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  /**
   * 导出为 DXF 格式 (CAD)
   */
  exportToDXF(): Blob {
    let dxf = this.getDXFHeader();

    // 添加组件
    for (const comp of this.project.components) {
      dxf += this.getDXFComponent(comp);
    }

    // 添加导线
    for (const wire of this.project.wires) {
      dxf += this.getDXFWire(wire);
    }

    // 添加网络标签
    for (const net of this.project.nets) {
      if (net.name) {
        dxf += this.getDXFText(net.name, 0, 0, 0.5); // 简化处理
      }
    }

    dxf += this.getDXFFooter();

    return new Blob([dxf], { type: 'application/dxf' });
  }

  /**
   * 导出为 SVG
   */
  exportToSVG(width: number = 800, height: number = 600): string {
    const svgNS = 'http://www.w3.org/2000/svg';

    let svg = `<svg xmlns="${svgNS}" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">\n`;
    svg += `  <style>\n`;
    svg += `    .component { stroke: #00ff88; stroke-width: 2; fill: none; }\n`;
    svg += `    .wire { stroke: #00ff88; stroke-width: 2; }\n`;
    svg += `    .pin { fill: #e94560; }\n`;
    svg += `    .label { fill: #ffffff; font-family: monospace; font-size: 12px; }\n`;
    svg += `    .net-label { fill: #ffcc00; font-family: monospace; font-size: 10px; }\n`;
    svg += `  </style>\n`;

    // 网格背景
    svg += `  <defs>\n`;
    svg += `    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">\n`;
    svg += `      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#2a2a4a" stroke-width="0.5"/>\n`;
    svg += `    </pattern>\n`;
    svg += `  </defs>\n`;
    svg += `  <rect width="100%" height="100%" fill="url(#grid)"/>\n`;

    // 绘制导线
    for (const wire of this.project.wires) {
      const pts = wire.points;
      if (pts.length >= 4) {
        const pointsStr = [];
        for (let i = 0; i < pts.length; i += 2) {
          pointsStr.push(`${pts[i]},${pts[i + 1]}`);
        }
        svg += `  <polyline points="${pointsStr.join(' ')}" class="wire" fill="none" stroke-linecap="round" stroke-linejoin="round"/>\n`;
      }
    }

    // 绘制组件占位符 (实际需要导入符号)
    for (const comp of this.project.components) {
      svg += `  <g transform="translate(${comp.x}, ${comp.y}) rotate(${comp.rotation})">\n`;
      svg += `    <rect x="-30" y="-30" width="60" height="60" class="component" stroke-dasharray="5,5"/>\n`;
      svg += `    <text x="0" y="45" text-anchor="middle" class="label">${comp.reference}</text>\n`;
      svg += `    <text x="0" y="55" text-anchor="middle" class="label">${comp.value}</text>\n`;
      svg += `  </g>\n`;
    }

    // 网络标签
    for (const net of this.project.nets) {
      if (net.name) {
        const firstPin = net.pins[0];
        if (firstPin) {
          svg += `  <text x="0" y="0" class="net-label">${net.name}</text>\n`;
        }
      }
    }

    svg += '</svg>';

    return svg;
  }

  /**
   * 导出为 PNG (需要 SVG 转 Canvas)
   */
  async exportToPNG(width: number = 800, height: number = 600): Promise<Blob> {
    const svg = this.exportToSVG(width, height);
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);

    const img = new Image();
    const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    return new Promise((resolve, reject) => {
      img.onload = () => {
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);

        canvas.toBlob((blob) => {
          if (blob) resolve(blob);
          else reject(new Error('Failed to create PNG blob'));
        }, 'image/png');
      };
      img.onerror = reject;
      img.src = url;
    });
  }

  // ==================== DXF 辅助方法 ====================

  private getDXFHeader(): string {
    return `0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
ENTITIES
`;
  }

  private getDXFFooter(): string {
    return `0
ENDSEC
0
EOF
`;
  }

  private getDXFComponent(comp: Component): string {
    // 输出组件边框 (简化为矩形)
    const halfW = 30;
    const halfH = 20;

    let dxf = `0
LINE
8
COMPONENTS
10
${comp.x - halfW}
20
${comp.y - halfH}
11
${comp.x + halfW}
21
${comp.y - halfH}
0
LINE
8
COMPONENTS
10
${comp.x + halfW}
20
${comp.y - halfH}
11
${comp.x + halfW}
21
${comp.y + halfH}
0
LINE
8
COMPONENTS
10
${comp.x + halfW}
20
${comp.y + halfH}
11
${comp.x - halfW}
21
${comp.y + halfH}
0
LINE
8
COMPONENTS
10
${comp.x - halfW}
20
${comp.y + halfH}
11
${comp.x - halfW}
21
${comp.y - halfH}
`;

    return dxf;
  }

  private getDXFWire(wire: Wire): string {
    const pts = wire.points;
    let dxf = '';
    for (let i = 0; i < pts.length - 2; i += 2) {
      dxf += `0
LINE
8
WIRES
10
${pts[i]}
20
${pts[i + 1]}
11
${pts[i + 2]}
21
${pts[i + 3]}
`;
    }
    return dxf;
  }

  private getDXFText(text: string, x: number, y: number, height: number): string {
    return `0
TEXT
8
LABELS
10
${x}
20
${y}
40
${height}
1
${text}
`;
  }
}

/**
 * 导出项目为指定格式
 */
export async function exportProject(
  project: ProjectState,
  format: 'ad-json' | 'lceda-json' | 'dxf' | 'svg' | 'png' | 'pdf',
  filename: string = 'schematic'
): Promise<void> {
  const service = new ExportService(project);

  switch (format) {
    case 'ad-json':
      saveAs(service.exportToAD(), `${filename}.json`);
      break;

    case 'lceda-json':
      saveAs(service.exportToLCEDA(), `${filename}.json`);
      break;

    case 'dxf':
      saveAs(service.exportToDXF(), `${filename}.dxf`);
      break;

    case 'svg':
      {
        const svg = service.exportToSVG(1200, 800);
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        saveAs(blob, `${filename}.svg`);
      }
      break;

    case 'png':
      {
        const blob = await service.exportToPNG(1200, 800);
        saveAs(blob, `${filename}.png`);
      }
      break;

    default:
      console.warn(`Export format ${format} not implemented`);
  }
}
