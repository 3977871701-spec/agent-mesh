# Schematic Designer - 开发计划

## 项目信息
- **项目名称**: Schematic Designer (自动原理图设计工具)
- **技术栈**: React 18 + TypeScript + Vite, Zustand, SVG + Custom Canvas, TailwindCSS, JSZip
- **输出目录**: /Users/xylei/agent-mesh/projects/schematic-designer
- **架构模式**: UI Layer → Service Layer → Data Layer (三层分离)

---

## 项目结构设计

```
schematic-designer/
├── src/
│   ├── main.tsx                      # 入口
│   ├── App.tsx                       # 根组件
│   ├── components/                   # UI 组件层
│   │   ├── InputPanel/               # 输入面板 (文本描述/参数化配置)
│   │   ├── CanvasEditor/             # 原理图画布编辑器
│   │   ├── BOMPanel/                 # BOM 表面板
│   │   ├── RuleCheckerPanel/         # 规则检查面板
│   │   ├── Toolbar/                  # 工具栏
│   │   ├── FileImportDialog/         # 文件导入对话框
│   │   └── ExportDialog/             # 导出对话框
│   ├── services/                     # 服务层
│   │   ├── ParseService/             # 文件解析 (AD/LCEDA)
│   │   ├── DesignRuleService/         # 设计规则检查
│   │   ├── ExportService/             # 导出服务 (DXF/SVG/PNG/PDF)
│   │   ├── BOMService/                # BOM 表生成
│   │   └── SimulationService/         # 仿真验证
│   ├── store/                        # 状态管理 (Zustand)
│   │   ├── schematicStore.ts         # 原理图状态
│   │   ├── componentLibraryStore.ts   # 器件库状态
│   │   └── uiStore.ts                # UI 状态
│   ├── data/                         # 数据层
│   │   ├── ComponentLibrary/         # 基础器件库定义
│   │   ├── SchematicData/            # 原理图数据结构
│   │   └── ProjectState/             # 项目状态模型
│   ├── utils/                        # 工具函数
│   │   ├── fileParser.ts             # 文件解析工具
│   │   ├── electricalRules.ts        # 电气规则工具
│   │   └── exporters/                # 导出工具 (DXF/SVG/PNG)
│   └── types/                        # TypeScript 类型定义
│       ├── component.ts             # 器件类型
│       ├── schematic.ts             # 原理图类型
│       └── project.ts               # 项目类型
├── public/                           # 静态资源
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── SPEC.md                          # 功能规格说明
```

---

## 技术栈选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | React 18 + TypeScript | 类型安全，生态成熟 |
| 构建工具 | Vite | 快速开发体验 |
| 状态管理 | Zustand | 轻量级，比 Redux 简洁 |
| 图形渲染 | SVG + Custom Canvas | 矢量图形 + 交互能力 |
| 样式 | TailwindCSS | 原子化 CSS，快速开发 |
| 文件解析 | JSZip | 处理 AD/LCEDA 压缩格式 |
| 导出格式 | SVG (原生) / Canvas2D (PNG/DXF) | 多格式支持 |

---

## 模块划分

### 前端模块 (UI Layer)

| 模块 | 职责 |
|------|------|
| InputPanel | 文本描述输入、参数化配置界面 |
| CanvasEditor | SVG 画布，器件渲染、拖拽、连线 |
| Toolbar | 工具栏：选择、连线、器件、撤销/重做 |
| FileImportDialog | AD/LCEDA 文件导入 |
| ExportDialog | 导出格式选择 (DXF/SVG/PNG/PDF) |
| BOMPanel | BOM 表展示与编辑 |
| RuleCheckerPanel | 电气规则检查结果显示 |

### 服务层模块 (Service Layer)

| 模块 | 职责 |
|------|------|
| ParseService | 解析 AD (.SchDoc JSON) / LCEDA (.json) 文件 |
| DesignRuleService | 电压/电流/连线规则检查 |
| ExportService | DXF/SVG/PNG/PDF 导出逻辑 |
| BOMService | BOM 表提取与生成 |
| SimulationService | 连通性/短路/开路验证 |

### 数据层模块 (Data Layer)

| 模块 | 职责 |
|------|------|
| ComponentLibrary | 内置基础器件 (R/C/L/D/LED/Q/MOSFET/U/V/GND/J) |
| SchematicData | 原理图数据模型 (components/nets/wires) |
| ProjectState | 项目整体状态模型 |

---

## 任务拆解

### Phase 1: 已完成
- [x] task-01: SPEC.md 功能规格文档
- [x] task-02: package.json 依赖配置
- [x] task-03: TypeScript + Vite + TailwindCSS 配置
- [x] task-04: Zustand 状态管理 (schematicStore.ts)
- [x] task-05: 器件符号 SVG 库 (symbols.tsx)
- [x] task-06: 设计规则检查服务 (designRuleChecker.ts)
- [x] task-07: BOM 生成服务 (bomGenerator.ts)
- [x] task-08: 导出服务 (exportService.ts)
- [x] task-09: 解析服务 (parseService.ts)
- [x] task-10: 主组件 App.tsx
- [x] task-11: 输入面板 (文本描述/参数化/文件导入)
- [x] task-12: 画布面板 (SVG 渲染)
- [x] task-13: BOM 面板
- [x] task-14: 规则检查面板
- [x] task-15: TypeScript 编译检查
- [x] task-16: 构建验证
- [x] task-17: 端口连通性测试

### Phase 2: 增强功能 (TODO)

#### 前端增强 (共 5 任务)
- [ ] **task-fe-01**: CanvasEditor 交互增强 - 器件拖拽调整、网格吸附、多选操作
- [ ] **task-fe-02**: Toolbar 完善 - 撤销/重做、缩放平移、网格切换
- [ ] **task-fe-03**: InputPanel 增强 - 自然语言描述解析为原理图逻辑
- [ ] **task-fe-04**: ExportDialog 完善 - DXF/PDF 导出预览
- [ ] **task-fe-05**: 响应式布局与深色模式支持

#### 服务层增强 (共 4 任务)
- [ ] **task-svc-01**: ParseService 增强 - 支持 .SchDoc 压缩包解析 (JSZip)
- [ ] **task-svc-02**: DesignRuleService 增强 - IC 供电电压范围检查 (datasheet 规则)
- [ ] **task-svc-03**: ExportService 增强 - DXF 导出完善，支持线宽/图层
- [ ] **task-svc-04**: SimulationService 完善 - 基础仿真验证逻辑

#### 数据层完善 (共 2 任务)
- [ ] **task-data-01**: TypeScript 类型定义完善 - component.ts / schematic.ts / project.ts
- [ ] **task-data-02**: 器件库扩充 - 添加更多器件类型与属性

---

## 执行顺序

### Phase 1: 已完成 (17 任务)
基础框架、核心服务、UI 组件已实现，可运行应用已就绪。

### Phase 2: 增强功能 (按优先级)

**优先级 P0 - 用户体验核心**
1. task-fe-01: CanvasEditor 交互增强
2. task-fe-02: Toolbar 完善
3. task-svc-01: ParseService 增强

**优先级 P1 - 功能完善**
4. task-fe-03: InputPanel 自然语言解析
5. task-svc-02: DesignRuleService IC 规则检查
6. task-svc-03: ExportService DXF 完善

**优先级 P2 - 体验优化**
7. task-fe-04: ExportDialog 导出预览
8. task-fe-05: 响应式与深色模式
9. task-svc-04: SimulationService 仿真验证
10. task-data-01: 类型定义完善
11. task-data-02: 器件库扩充

---

## 任务统计

| 类别 | 已完成 | 待完成 |
|------|--------|--------|
| Phase 1 基础 | 17 | 0 |
| 前端增强 | 0 | 5 |
| 服务层增强 | 0 | 4 |
| 数据层完善 | 0 | 2 |
| **合计** | **17** | **11** |

---

## 交付物
1. SPEC.md - 功能规格
2. dev-plan.md - 开发计划
3. 完整的可运行 React 应用 (Phase 1)
4. 增强功能 (Phase 2)
