# 经验沉淀

此文件记录开发过程中遇到的问题和解决方案。

---

## 260508 1430 - React + Vite 项目初始化

### 遇到的问题
- Vite 项目创建后，TypeScript 配置需要额外创建 tsconfig.node.json
- Zustand store 中使用 uuid 需要正确导入

### 解决方案
- 使用 `npm create vite@latest` 创建项目，选择 React + TypeScript 模板
- Vite 配置文件中使用 `@vitejs/plugin-react` 插件

### 注意事项
- 确保 tsconfig.json 中的 `moduleResolution` 设置为 `bundler`
- uuid 导入使用 `import { v4 as uuidv4 } from 'uuid'`

---

## 260508 1500 - SVG 器件符号渲染

### 遇到的问题
- 器件符号需要支持旋转和位置变换
- 引脚位置计算需要考虑旋转角度

### 解决方案
- 使用 SVG `transform` 属性实现旋转：`transform="translate(x, y) rotate(angle)"`
- 引脚相对位置在组件内部定义，父组件传入绝对坐标

### 代码示例
```tsx
const SymbolComponent = ({ x, y, rotation = 0 }) => (
  <g transform={`translate(${x}, ${y}) rotate(${rotation})`}>
    {/* 符号内容 */}
  </g>
);
```

### 注意事项
- SVG 变换顺序：先平移后旋转
- 引脚名称使用 `className="pin-label"` 设置样式

---

## 260508 1515 - 设计规则检查实现

### 遇到的问题
- 需要检查多种电气规则：悬空引脚、短路、开路、电压等级等
- 规则检查需要访问完整的项目状态

### 解决方案
- 创建 `DesignRuleChecker` 类，接收 `ProjectState` 作为输入
- 每条规则独立方法实现，最后通过 `checkAll()` 汇总
- 使用 `RuleViolation` 接口记录违规信息

### 注意事项
- 电压/电阻/电流解析需要处理单位后缀 (kΩ, mA, etc.)
- 安全系数 1.5 用于电压等级检查

---

## 260508 1600 - CanvasEditor SVG 交互实现

### 遇到的问题
- SVG 画布需要支持拖拽、缩放、多选等复杂交互
- 网格吸附需要考虑缩放比例
- 多选操作需要维护选中状态

### 解决方案
- 使用 `createSVGPoint()` 和 `getScreenCTM()` 进行鼠标坐标到 SVG 坐标的转换
- 将缩放和平移应用到 transform group 上
- 使用 Zustand store 独立管理 UI 状态（选中、悬停、工具模式）

### 代码示例
```tsx
const getMousePosition = (e: React.MouseEvent) => {
  const pt = svgRef.current.createSVGPoint();
  pt.x = e.clientX;
  pt.y = e.clientY;
  const svgP = pt.matrixTransform(svgRef.current.getScreenCTM()?.inverse());
  return { x: (svgP.x - ui.panX) / ui.zoom, y: (svgP.y - ui.panY) / ui.zoom };
};
```

### 注意事项
- SVG 变换顺序：先平移后缩放
- 拖拽时需要保存起始位置计算 delta

---

## 260508 1615 - Undo/Redo 历史记录实现

### 遇到的问题
- 需要在状态变化时保存历史快照
- 历史记录需要限制大小防止内存溢出
- 需要正确处理撤销/重做的边界条件

### 解决方案
- 在 schematicStore 中添加 `history` 数组和 `historyIndex`
- 每次修改操作前调用 `saveHistory()` 保存当前状态
- `undo()`/`redo()` 通过修改 `historyIndex` 恢复状态

### 注意事项
- `loadProject` 应该清空历史记录
- `saveHistory` 时需要截断重做历史（新的操作覆盖重做栈）

---

## 260508 1630 - JSZip 解析 .SchDoc 压缩包

### 遇到的问题
- Altium Designer 的 .SchDoc 文件是 ZIP 压缩包格式
- 需要异步解压后解析内部 JSON 文件

### 解决方案
- 使用 `JSZip.loadAsync()` 加载 ArrayBuffer
- 遍历 ZIP 中的文件，查找 `.sch.json` 或包含 `schematic` 的文件
- 支持 ArrayBuffer 和文本两种解析方式

### 代码示例
```typescript
async parseFromSchDoc(fileContent: ArrayBuffer): Promise<Partial<ProjectState>> {
  const zip = await JSZip.loadAsync(fileContent);
  // 遍历文件并解析
}
```

### 注意事项
- `.SchDoc` 和 `.SchArc` 是压缩包格式，需要用 `arrayBuffer()` 读取
- 解析失败的文件应跳过，不影响其他文件

---

## 260508 1700 - 导线绘制系统实现

### 遇到的问题
- 原理图工具缺少导线绘制功能，无法连接器件引脚
- 导线需要支持折线（多段）绘制
- 导线绘制状态需要与组件拖拽状态分开管理
- 更新 Wire 类型从简单线段改为折点数组格式

### 解决方案
- 创建 `wireService.ts`：提供导线绘制辅助函数（吸附、引脚检测、路径生成）
- 创建 `netService.ts`：提供网络管理功能（创建、合并、命名）
- 扩展 Wire 类型：`points: number[]` 支持折线 `[x1,y1,x2,y2,x3,y3,...]`
- CanvasEditor 添加 WireDrawingState 状态管理绘制过程
- 支持点击引脚开始/结束、双击结束、自由折点绘制

### 代码示例
```typescript
// 导线绘制状态
interface WireDrawingState {
  isDrawing: boolean;
  startPinId: string | null;
  waypoints: number[];
  currentX: number;
  currentY: number;
}

// 生成导线预览 SVG path
function generateWirePreviewPath(waypoints: number[], currentX: number, currentY: number): string {
  let path = `M ${waypoints[0]} ${waypoints[1]}`;
  for (let i = 2; i < waypoints.length; i += 2) {
    path += ` L ${waypoints[i]} ${waypoints[i + 1]}`;
  }
  path += ` L ${currentX} ${currentY}`;
  return path;
}
```

### 注意事项
- 修改 Wire 类型后需要同步更新 exportService.ts 和 parseService.ts
- 引脚位置计算需要考虑组件旋转角度
- 使用 `useCallback` 封装绘制函数避免不必要的重渲染
- `snapToGrid` 函数签名需要保持一致，避免调用处产生歧义

---

## 260508 1715 - TypeScript 类型扩展与迁移

### 遇到的问题
- 扩展现有类型（如 Wire）需要同步更新所有使用该类型的地方
- 枚举值比较时需要使用枚举而非字符串字面量

### 解决方案
- 修改 Wire 接口后，同步更新 exportService、parseService 的导线序列化/反序列化逻辑
- 使用 `ComponentType.GND` 而非 `'GND'` 进行枚举比较

### 注意事项
- 兼容旧格式：在 parseService 中同时支持旧格式 (x1/y1/x2/y2) 和新格式 (points 数组)
- 类型修改后立即运行 `npm run build` 验证所有消费者

