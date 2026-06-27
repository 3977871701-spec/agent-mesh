import React, { useState, useCallback, useRef } from 'react';
import { useSchematicStore } from './store/schematicStore';
import { ComponentNames, DefaultPins } from './assets/components/symbols';
import { ComponentType, Component as CompType } from './types';
import { checkDesignRules } from './services/designRuleChecker';
import { exportBOM, generateBOM } from './services/bomGenerator';
import { exportProject } from './services/exportService';
import { parseSchematicFile, generateFromDescription, parseSchematicFileAsync } from './services/parseService';
import { createLEDFlashingCircuit } from './examples/ledFlashingCircuit';
import { v4 as uuidv4 } from 'uuid';
import { saveAs } from 'file-saver';
import CanvasEditor from './components/CanvasEditor/CanvasEditor';
import Toolbar from './components/Toolbar/Toolbar';

const ComponentTypeList = Object.values(ComponentType);

export default function App() {
  const store = useSchematicStore();
  const [activeTab, setActiveTab] = useState<'input' | 'canvas' | 'bom' | 'rules'>('input');
  const [description, setDescription] = useState('');
  const [selectedType, setSelectedType] = useState<ComponentType>(ComponentType.RESISTOR);
  const [componentValue, setComponentValue] = useState('');
  const [importError, setImportError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 处理文本描述生成
  const handleGenerateFromDescription = useCallback(() => {
    if (!description.trim()) return;

    const parsed = generateFromDescription(description);
    store.loadProject(parsed);
    setActiveTab('canvas');
  }, [description, store]);

  // 处理文件导入 (支持 .SchDoc 压缩包和 JSON)
  const handleFileImport = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const filename = file.name.toLowerCase();

      // .SchDoc 和 .SchArc 是压缩包格式，需要用 ArrayBuffer
      if (filename.endsWith('.schdoc') || filename.endsWith('.scharc') || filename.endsWith('.sch')) {
        const buffer = await file.arrayBuffer();
        const parsed = await parseSchematicFileAsync(buffer, file.name);
        store.loadProject(parsed);
      } else {
        // JSON 格式用文本读取
        const reader = new FileReader();
        const content = await new Promise<string>((resolve, reject) => {
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsText(file);
        });
        const parsed = parseSchematicFile(content, file.name);
        store.loadProject(parsed);
      }

      setImportError('');
      setActiveTab('canvas');
    } catch (error) {
      setImportError(`导入失败: ${error}`);
    }
  }, [store]);

  // 添加器件
  const handleAddComponent = useCallback(() => {
    const pins = DefaultPins[selectedType]?.map((p, i) => ({
      id: uuidv4(),
      name: p.name,
      number: String(i + 1),
      x: -30 + i * 60,
      y: 0,
      direction: p.direction,
    })) || [];

    store.addComponent({
      type: selectedType,
      reference: store.generateReference(selectedType),
      value: componentValue || getDefaultValue(selectedType),
      x: 100 + Math.random() * 200,
      y: 100 + Math.random() * 200,
      rotation: 0,
      pins,
      properties: {},
    });
  }, [selectedType, componentValue, store]);

  // 运行设计规则检查
  const handleRunDRC = useCallback(() => {
    const violations = checkDesignRules(store);
    store.setViolations(violations);
  }, [store]);

  // 导出 BOM
  const handleExportBOM = useCallback((format: 'csv' | 'md' | 'tsv') => {
    const content = exportBOM(store, format);
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    saveAs(blob, `BOM_${store.name}.${format}`);
  }, [store]);

  // 导出原理图
  const handleExport = useCallback((format: 'ad-json' | 'lceda-json' | 'dxf' | 'svg' | 'png') => {
    exportProject(store, format, store.name);
  }, [store]);

  const bom = generateBOM(store);

  return (
    <div className="min-h-screen bg-gradient-to-br from-schematic-bg to-schematic-panel text-white">
      {/* 顶部导航 */}
      <header className="border-b border-schematic-accent bg-schematic-panel/80 backdrop-blur">
        <div className="container mx-auto px-4 py-3">
          <h1 className="text-xl font-bold text-schematic-highlight">
            Schematic Designer - 自动原理图设计工具
          </h1>
          <p className="text-sm text-gray-400">
            支持 AD / 嘉立创格式 | 电气规则检查 | BOM 生成
          </p>
        </div>
      </header>

      {/* 标签页 */}
      <div className="border-b border-schematic-accent">
        <div className="container mx-auto px-4">
          <nav className="flex gap-1">
            {(['input', 'canvas', 'bom', 'rules'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'text-schematic-highlight border-b-2 border-schematic-highlight'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab === 'input' && '📥 输入'}
                {tab === 'canvas' && '🎨 画布'}
                {tab === 'bom' && '📋 BOM'}
                {tab === 'rules' && '⚡ 规则'}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* 主内容 */}
      <main className="container mx-auto px-4 py-6">
        {/* 输入面板 */}
        {activeTab === 'input' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 文本描述输入 */}
            <div className="bg-schematic-panel rounded-lg p-6 border border-schematic-accent">
              <h2 className="text-lg font-semibold mb-4">📝 描述输入</h2>
              <p className="text-sm text-gray-400 mb-4">
                用自然语言描述你想要的电路，系统会自动生成原理图
              </p>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="例如：LED闪烁电路 / 电压分压器 / 运放放大电路 / 稳压电源"
                className="w-full h-32 bg-schematic-bg border border-schematic-accent rounded p-3 text-white placeholder-gray-500 focus:outline-none focus:border-schematic-highlight"
              />
              <button
                onClick={handleGenerateFromDescription}
                className="mt-4 px-6 py-2 bg-schematic-highlight text-white rounded hover:opacity-90 transition"
              >
                生成原理图
              </button>
            </div>

            {/* 参数化输入 */}
            <div className="bg-schematic-panel rounded-lg p-6 border border-schematic-accent">
              <h2 className="text-lg font-semibold mb-4">🔧 参数化输入</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">器件类型</label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value as ComponentType)}
                    className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-white"
                  >
                    {ComponentTypeList.map((type) => (
                      <option key={type} value={type}>
                        {ComponentNames[type]} ({type})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">参数值</label>
                  <input
                    type="text"
                    value={componentValue}
                    onChange={(e) => setComponentValue(e.target.value)}
                    placeholder={getDefaultValue(selectedType)}
                    className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-white"
                  />
                </div>

                <button
                  onClick={handleAddComponent}
                  className="w-full px-6 py-3 bg-schematic-accent text-white rounded hover:bg-schematic-accent/80 transition"
                >
                  ➕ 添加器件
                </button>
              </div>
            </div>

            {/* 文件导入 */}
            <div className="bg-schematic-panel rounded-lg p-6 border border-schematic-accent">
              <h2 className="text-lg font-semibold mb-4">📂 文件导入</h2>
              <p className="text-sm text-gray-400 mb-4">
                导入现有原理图文件 (AD JSON / 嘉立创 JSON)
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileImport}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-6 py-2 border border-schematic-highlight text-schematic-highlight rounded hover:bg-schematic-highlight/10 transition"
              >
                选择文件
              </button>
              {importError && (
                <p className="mt-2 text-sm text-red-400">{importError}</p>
              )}
            </div>

            {/* 快捷模板 */}
            <div className="bg-schematic-panel rounded-lg p-6 border border-schematic-accent">
              <h2 className="text-lg font-semibold mb-4">⚡ 快捷模板</h2>
              <div className="grid grid-cols-2 gap-2">
                {[
                  'LED闪烁电路',
                  '电压分压器',
                  '运放放大电路',
                  '稳压电源',
                  '滤波电路',
                  '驱动电路',
                ].map((template) => (
                  <button
                    key={template}
                    onClick={() => {
                      setDescription(template);
                      setActiveTab('input');
                    }}
                    className="px-3 py-2 bg-schematic-bg border border-schematic-accent rounded text-sm hover:border-schematic-highlight transition"
                  >
                    {template}
                  </button>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-schematic-accent/50">
                <button
                  onClick={() => {
                    console.log('[DEBUG] 点击了加载示例电路按钮');
                    const circuit = createLEDFlashingCircuit();
                    console.log('[DEBUG] 创建电路数据:', JSON.stringify(circuit, null, 2));
                    console.log('[DEBUG] 原始导线数量:', circuit.wires.length);
                    if (circuit.wires.length > 0) {
                      console.log('[DEBUG] 原始导线示例:', JSON.stringify(circuit.wires[0]));
                    }

                    // 为所有器件和导线生成新 ID
                    const idMap = new Map<string, string>();

                    const newComponents = circuit.components.map(comp => {
                      const newId = uuidv4();
                      idMap.set(comp.reference.toLowerCase(), newId);
                      return { ...comp, id: newId };
                    });

                    const newWires = circuit.wires.map(wire => ({
                      ...wire,
                      id: uuidv4(),
                    }));

                    const newNets = circuit.nets.map(net => ({
                      ...net,
                      id: uuidv4(),
                      pins: net.pins.map(pin => {
                        // 解析 pin 格式 "ref:pinId"
                        const [ref, localPinId] = pin.split(':');
                        const newRefId = idMap.get(ref.toLowerCase());
                        if (newRefId && localPinId) {
                          return `${newRefId}:${localPinId}`;
                        }
                        return pin;
                      }),
                    }));

                    console.log('[DEBUG] 处理后导线数量:', newWires.length);
                    console.log('[DEBUG] 处理后导线示例:', JSON.stringify(newWires[0]));
                    console.log('[DEBUG] 器件列表:', newComponents.map(c => c.reference));

                    store.loadProject({
                      name: 'LED闪烁电路 (NE555)',
                      components: newComponents,
                      wires: newWires,
                      nets: newNets,
                    });

                    // 延迟检查确保状态更新
                    setTimeout(() => {
                      console.log('[DEBUG] 延迟验证 - store.wires.length:', store.wires.length);
                    }, 100);

                    setActiveTab('canvas');
                  }}
                  className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded font-medium transition"
                >
                  加载示例电路 (NE555 LED闪烁)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 画布面板 */}
        {activeTab === 'canvas' && (
          <div className="flex flex-col gap-4">
            {/* 工具栏 */}
            <Toolbar onRunDRC={handleRunDRC} />

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
              {/* 器件列表 */}
              <div className="bg-schematic-panel rounded-lg p-4 border border-schematic-accent">
                <h3 className="font-semibold mb-3">器件列表 ({store.components.length})</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {store.components.map((comp) => (
                    <div
                      key={comp.id}
                      className={`p-2 bg-schematic-bg rounded cursor-pointer hover:bg-schematic-accent ${
                        store.selectedComponent === comp.id ? 'ring-2 ring-schematic-highlight' : ''
                      }`}
                      onClick={() => store.selectComponent(comp.id)}
                    >
                      <div className="font-medium">{comp.reference}</div>
                      <div className="text-xs text-gray-400">
                        {ComponentNames[comp.type]} | {comp.value}
                      </div>
                    </div>
                  ))}
                </div>
                {store.components.length > 0 && (
                  <button
                    onClick={() => store.selectComponent(undefined)}
                    className="mt-3 w-full py-2 text-sm text-gray-400 border border-schematic-accent rounded"
                  >
                    取消选择
                  </button>
                )}
              </div>

              {/* 画布编辑器 */}
              <div className="lg:col-span-2 bg-schematic-panel rounded-lg border border-schematic-accent overflow-hidden flex flex-col">
                <div className="p-2 border-b border-schematic-accent flex justify-between items-center shrink-0">
                  <span className="text-sm">{store.name}</span>
                  <span className="text-xs text-gray-400">
                    {store.wires.length} 导线 | {store.violations.length} 违规
                  </span>
                </div>
                <div className="h-[500px]">
                  <CanvasEditor />
                </div>
              </div>

              {/* 属性面板 */}
              <div className="bg-schematic-panel rounded-lg p-4 border border-schematic-accent">
                <h3 className="font-semibold mb-3">属性</h3>
                {store.selectedComponent ? (
                  <ComponentProperties
                    component={store.components.find((c) => c.id === store.selectedComponent)!}
                    onUpdate={(updates) =>
                      store.updateComponent(store.selectedComponent!, updates)
                    }
                    onDelete={() => store.removeComponent(store.selectedComponent!)}
                  />
                ) : (
                  <p className="text-sm text-gray-400">选择器件查看属性</p>
                )}

                <div className="mt-6">
                  <h4 className="text-sm font-medium mb-2">导出</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <button onClick={() => handleExport('ad-json')} className="px-2 py-1 text-xs border border-schematic-accent rounded">
                      AD 格式
                    </button>
                    <button onClick={() => handleExport('lceda-json')} className="px-2 py-1 text-xs border border-schematic-accent rounded">
                      嘉立创
                    </button>
                    <button onClick={() => handleExport('dxf')} className="px-2 py-1 text-xs border border-schematic-accent rounded">
                      DXF
                    </button>
                    <button onClick={() => handleExport('svg')} className="px-2 py-1 text-xs border border-schematic-accent rounded">
                      SVG
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* BOM 面板 */}
        {activeTab === 'bom' && (
          <div className="bg-schematic-panel rounded-lg p-6 border border-schematic-accent">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">📋 物料清单 (BOM)</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => handleExportBOM('csv')}
                  className="px-4 py-2 text-sm bg-green-600 text-white rounded"
                >
                  导出 CSV
                </button>
                <button
                  onClick={() => handleExportBOM('md')}
                  className="px-4 py-2 text-sm bg-schematic-accent text-white rounded"
                >
                  导出 MD
                </button>
              </div>
            </div>

            {bom.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-schematic-accent">
                      <th className="text-left py-2 px-3">编号</th>
                      <th className="text-left py-2 px-3">类型</th>
                      <th className="text-left py-2 px-3">参数值</th>
                      <th className="text-left py-2 px-3">数量</th>
                      <th className="text-left py-2 px-3">封装</th>
                      <th className="text-left py-2 px-3">描述</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bom.map((item, index) => (
                      <tr key={index} className="border-b border-schematic-accent/50 hover:bg-schematic-accent/20">
                        <td className="py-2 px-3">{index + 1}</td>
                        <td className="py-2 px-3">{item.type}</td>
                        <td className="py-2 px-3 font-mono">{item.value}</td>
                        <td className="py-2 px-3">{item.quantity}</td>
                        <td className="py-2 px-3">{item.footprint}</td>
                        <td className="py-2 px-3 text-gray-400">{item.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">
                暂无器件，请先添加或导入原理图
              </p>
            )}
          </div>
        )}

        {/* 规则面板 */}
        {activeTab === 'rules' && (
          <div className="bg-schematic-panel rounded-lg p-6 border border-schematic-accent">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">⚡ 设计规则检查</h2>
              <button
                onClick={handleRunDRC}
                className="px-4 py-2 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700"
              >
                重新检查
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-schematic-bg p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-400">
                  {store.violations.filter((v) => v.severity !== 'error').length}
                </div>
                <div className="text-sm text-gray-400">警告</div>
              </div>
              <div className="bg-schematic-bg p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-400">
                  {store.violations.filter((v) => v.severity === 'error').length}
                </div>
                <div className="text-sm text-gray-400">错误</div>
              </div>
              <div className="bg-schematic-bg p-4 rounded-lg">
                <div className="text-2xl font-bold text-white">
                  {store.violations.length === 0 ? '✓' : store.violations.length}
                </div>
                <div className="text-sm text-gray-400">
                  {store.violations.length === 0 ? '全部通过' : '问题总数'}
                </div>
              </div>
            </div>

            {store.violations.length > 0 ? (
              <div className="space-y-2">
                {store.violations.map((v) => (
                  <div
                    key={v.id}
                    className={`p-3 rounded-lg border ${
                      v.severity === 'error'
                        ? 'bg-red-900/20 border-red-500'
                        : 'bg-yellow-900/20 border-yellow-500'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{v.severity === 'error' ? '❌' : '⚠️'}</span>
                      <span className="font-medium">{v.rule}</span>
                    </div>
                    <p className="mt-1 text-sm text-gray-300">{v.message}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <div className="text-4xl mb-2">✓</div>
                <p>设计规则检查通过，无违规项</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

// 器件属性组件
function ComponentProperties({
  component,
  onUpdate,
  onDelete,
}: {
  component: CompType;
  onUpdate: (updates: Partial<CompType>) => void;
  onDelete: () => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs text-gray-400 mb-1">编号</label>
        <input
          type="text"
          value={component.reference}
          onChange={(e) => onUpdate({ reference: e.target.value })}
          className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-sm"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">参数值</label>
        <input
          type="text"
          value={component.value}
          onChange={(e) => onUpdate({ value: e.target.value })}
          className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-sm"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">X 坐标</label>
        <input
          type="number"
          value={component.x}
          onChange={(e) => onUpdate({ x: parseInt(e.target.value) || 0 })}
          className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-sm"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Y 坐标</label>
        <input
          type="number"
          value={component.y}
          onChange={(e) => onUpdate({ y: parseInt(e.target.value) || 0 })}
          className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-sm"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">旋转</label>
        <select
          value={component.rotation}
          onChange={(e) => onUpdate({ rotation: parseInt(e.target.value) })}
          className="w-full bg-schematic-bg border border-schematic-accent rounded p-2 text-sm"
        >
          <option value={0}>0°</option>
          <option value={90}>90°</option>
          <option value={180}>180°</option>
          <option value={270}>270°</option>
        </select>
      </div>
      <button
        onClick={onDelete}
        className="w-full py-2 text-sm text-red-400 border border-red-500 rounded hover:bg-red-500/20"
      >
        删除器件
      </button>
    </div>
  );
}

// 获取器件默认值
function getDefaultValue(type: ComponentType): string {
  const defaults: Partial<Record<ComponentType, string>> = {
    [ComponentType.RESISTOR]: '10kΩ',
    [ComponentType.CAPACITOR]: '100nF',
    [ComponentType.INDUCTOR]: '10uH',
    [ComponentType.DIODE]: '1N4148',
    [ComponentType.LED]: 'Red',
    [ComponentType.NPN_TRANSISTOR]: '2N2222',
    [ComponentType.PNP_TRANSISTOR]: '2N2907',
    [ComponentType.NMOS]: '2N7000',
    [ComponentType.PMOS]: 'IRF540',
    [ComponentType.OPAMP]: 'LM358',
    [ComponentType.VOLTAGE_SOURCE]: '5V',
    [ComponentType.CURRENT_SOURCE]: '1A',
    [ComponentType.CONNECTOR]: '3P',
  };
  return defaults[type] || '';
}
