import { create } from 'zustand';

type ToolMode = 'select' | 'wire' | 'pan';

interface UIState {
  // Canvas state
  zoom: number;
  panX: number;
  panY: number;
  toolMode: ToolMode;
  gridVisible: boolean;
  snapToGrid: boolean;
  gridSize: number;

  // Selection
  selectedComponents: string[];
  hoveredComponent: string | null;

  // Actions
  setZoom: (zoom: number) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
  setPan: (x: number, y: number) => void;
  setToolMode: (mode: ToolMode) => void;
  toggleGrid: () => void;
  toggleSnap: () => void;
  setGridSize: (size: number) => void;
  setSelectedComponents: (ids: string[]) => void;
  addToSelection: (id: string) => void;
  removeFromSelection: (id: string) => void;
  clearSelection: () => void;
  toggleSelection: (id: string) => void;
  setHoveredComponent: (id: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  zoom: 1,
  panX: 0,
  panY: 0,
  toolMode: 'select',
  gridVisible: true,
  snapToGrid: true,
  gridSize: 20,
  selectedComponents: [],
  hoveredComponent: null,

  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),

  zoomIn: () => set((state) => ({ zoom: Math.min(5, state.zoom * 1.2) })),

  zoomOut: () => set((state) => ({ zoom: Math.max(0.1, state.zoom / 1.2) })),

  resetZoom: () => set({ zoom: 1, panX: 0, panY: 0 }),

  setPan: (x, y) => set({ panX: x, panY: y }),

  setToolMode: (mode) => set({ toolMode: mode }),

  toggleGrid: () => set((state) => ({ gridVisible: !state.gridVisible })),

  toggleSnap: () => set((state) => ({ snapToGrid: !state.snapToGrid })),

  setGridSize: (size) => set({ gridSize: Math.max(5, Math.min(100, size)) }),

  setSelectedComponents: (ids) => set({ selectedComponents: ids }),

  addToSelection: (id) => set((state) => ({
    selectedComponents: state.selectedComponents.includes(id)
      ? state.selectedComponents
      : [...state.selectedComponents, id]
  })),

  removeFromSelection: (id) => set((state) => ({
    selectedComponents: state.selectedComponents.filter((cid) => cid !== id)
  })),

  clearSelection: () => set({ selectedComponents: [] }),

  toggleSelection: (id) => set((state) => ({
    selectedComponents: state.selectedComponents.includes(id)
      ? state.selectedComponents.filter((cid) => cid !== id)
      : [...state.selectedComponents, id]
  })),

  setHoveredComponent: (id) => set({ hoveredComponent: id }),
}));
