import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import {
  Component,
  Net,
  Wire,
  RuleViolation,
  ComponentType,
} from '../types';

interface HistoryState {
  components: Component[];
  nets: Net[];
  wires: Wire[];
}

interface SchematicStore {
  // Data
  name: string;
  components: Component[];
  nets: Net[];
  wires: Wire[];
  violations: RuleViolation[];
  gridSize: number;
  snapToGrid: boolean;
  selectedComponent: string | undefined;

  // History
  history: HistoryState[];
  historyIndex: number;
  maxHistorySize: number;

  // Actions
  addComponent: (component: Omit<Component, 'id'>) => string;
  removeComponent: (id: string) => void;
  updateComponent: (id: string, updates: Partial<Component>) => void;
  selectComponent: (id: string | undefined) => void;

  addNet: (net: Omit<Net, 'id'>) => string;
  removeNet: (id: string) => void;

  addWire: (wire: Omit<Wire, 'id'>) => string;
  removeWire: (id: string) => void;

  setViolations: (violations: RuleViolation[]) => void;
  clearViolations: () => void;

  setGridSize: (size: number) => void;
  toggleSnapToGrid: () => void;

  loadProject: (data: {
    name?: string;
    components?: Component[];
    wires?: Wire[];
    nets?: Net[];
    violations?: RuleViolation[];
    gridSize?: number;
    snapToGrid?: boolean;
  }) => void;
  resetProject: () => void;

  // Undo/Redo
  undo: () => void;
  redo: () => void;
  saveHistory: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;

  // 生成引用编号
  generateReference: (type: ComponentType) => string;
}

export const useSchematicStore = create<SchematicStore>((set, get) => ({
  // Initial data state
  name: '未命名原理图',
  components: [],
  nets: [],
  wires: [],
  violations: [],
  gridSize: 20,
  snapToGrid: true,
  selectedComponent: undefined,

  // History state
  history: [],
  historyIndex: -1,
  maxHistorySize: 50,

  addComponent: (component) => {
    const id = uuidv4();
    const reference = component.reference || get().generateReference(component.type);
    get().saveHistory();
    set((state) => ({
      components: [...state.components, { ...component, id, reference }],
      historyIndex: state.historyIndex + 1,
    }));
    return id;
  },

  removeComponent: (id) => {
    get().saveHistory();
    set((state) => ({
      components: state.components.filter((c) => c.id !== id),
      nets: state.nets.filter((n) => !n.pins.some((p) => p.includes(id))),
      selectedComponent: state.selectedComponent === id ? undefined : state.selectedComponent,
      historyIndex: state.historyIndex + 1,
    }));
  },

  updateComponent: (id, updates) => {
    get().saveHistory();
    set((state) => ({
      components: state.components.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
      historyIndex: state.historyIndex + 1,
    }));
  },

  selectComponent: (id) => {
    set({ selectedComponent: id });
  },

  addNet: (net) => {
    const id = uuidv4();
    get().saveHistory();
    set((state) => ({
      nets: [...state.nets, { ...net, id }],
      historyIndex: state.historyIndex + 1,
    }));
    return id;
  },

  removeNet: (id) => {
    get().saveHistory();
    set((state) => ({
      nets: state.nets.filter((n) => n.id !== id),
      historyIndex: state.historyIndex + 1,
    }));
  },

  addWire: (wire) => {
    const id = uuidv4();
    get().saveHistory();
    set((state) => ({
      wires: [...state.wires, { ...wire, id }],
      historyIndex: state.historyIndex + 1,
    }));
    console.log('[DEBUG] addWire - wires count:', get().wires.length);
    return id;
  },

  removeWire: (id) => {
    get().saveHistory();
    set((state) => ({
      wires: state.wires.filter((w) => w.id !== id),
      historyIndex: state.historyIndex + 1,
    }));
  },

  setViolations: (violations) => {
    set({ violations });
  },

  clearViolations: () => {
    set({ violations: [] });
  },

  setGridSize: (size) => {
    set({ gridSize: size });
  },

  toggleSnapToGrid: () => {
    set((state) => ({ snapToGrid: !state.snapToGrid }));
  },

  loadProject: (data) => {
    console.log('[DEBUG loadProject] 收到数据:', {
      components: data.components?.length || 0,
      wires: data.wires?.length || 0,
      nets: data.nets?.length || 0
    });

    const newState = {
      name: data.name || '未命名原理图',
      components: data.components || [],
      wires: data.wires || [],
      nets: data.nets || [],
      violations: data.violations || [],
      gridSize: data.gridSize || 20,
      snapToGrid: data.snapToGrid !== undefined ? data.snapToGrid : true,
      selectedComponent: undefined,
      history: [],
      historyIndex: -1,
    };

    console.log('[DEBUG loadProject] 设置状态, wires:', newState.wires.length);
    set(newState);

    // 验证状态更新
    const state = get();
    console.log('[DEBUG loadProject] 验证 - store.wires.length:', state.wires.length);
  },

  resetProject: () => {
    set({
      name: '未命名原理图',
      components: [],
      nets: [],
      wires: [],
      violations: [],
      gridSize: 20,
      snapToGrid: true,
      selectedComponent: undefined,
      history: [],
      historyIndex: -1,
    });
  },

  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex < 0 || history.length === 0) return;

    const prevState = history[historyIndex];
    set({
      components: [...prevState.components],
      nets: [...prevState.nets],
      wires: [...prevState.wires],
      historyIndex: historyIndex - 1,
    });
  },

  redo: () => {
    const { history, historyIndex } = get();
    if (historyIndex >= history.length - 1) return;

    const nextState = history[historyIndex + 1];
    set({
      components: [...nextState.components],
      nets: [...nextState.nets],
      wires: [...nextState.wires],
      historyIndex: historyIndex + 1,
    });
  },

  saveHistory: () => {
    const state = get();
    const { history, historyIndex, maxHistorySize } = state;
    const currentHistory: HistoryState = {
      components: [...state.components],
      nets: [...state.nets],
      wires: [...state.wires],
    };

    // Remove any redo states
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(currentHistory);

    // Limit history size
    if (newHistory.length > maxHistorySize) {
      newHistory.shift();
    }

    set({
      history: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },

  canUndo: () => get().historyIndex >= 0,

  canRedo: () => {
    const { history, historyIndex } = get();
    return historyIndex < history.length - 1;
  },

  generateReference: (type) => {
    const { components } = get();
    const prefix = type;
    const existingRefs = components
      .filter((c) => c.type === type)
      .map((c) => {
        const match = c.reference.match(new RegExp(`^${type}(\\d+)$`));
        return match ? parseInt(match[1], 10) : 0;
      });
    const maxRef = Math.max(0, ...existingRefs);
    return `${prefix}${maxRef + 1}`;
  },
}));
