import React from 'react';
import { useSchematicStore } from '../../store/schematicStore';
import { useUIStore } from '../../store/uiStore';

interface ToolbarProps {
  onRunDRC?: () => void;
}

export default function Toolbar({ onRunDRC }: ToolbarProps) {
  const store = useSchematicStore();
  const ui = useUIStore();

  return (
    <div className="flex items-center justify-between bg-schematic-panel border-b border-schematic-accent px-4 py-2">
      {/* Left section - Tools */}
      <div className="flex items-center gap-1">
        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M3 2a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2zm1 0v8h8V2H4z" />
              <path d="M6 5h4v1H6V5zm0 2h4v1H6V7zm0 2h2v1H6V9z" />
            </svg>
          }
          label="选择"
          active={ui.toolMode === 'select'}
          onClick={() => ui.setToolMode('select')}
          title="选择工具 (V)"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M2 2v12h12V2H2zm1 1h10v10H3V3z" />
              <path d="M5 8h6v1H5V8z" />
            </svg>
          }
          label="导线"
          active={ui.toolMode === 'wire'}
          onClick={() => ui.setToolMode('wire')}
          title="导线工具 (W)"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2zm0 1a5 5 0 1 1 0 10A5 5 0 0 1 8 3z" />
              <path d="M8 5v3l2 1" stroke="currentColor" strokeWidth="1.5" fill="none" />
            </svg>
          }
          label="平移"
          active={ui.toolMode === 'pan'}
          onClick={() => ui.setToolMode('pan')}
          title="平移工具 (H)"
        />

        <div className="w-px h-6 bg-schematic-accent mx-2" />

        {/* Undo/Redo */}
        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 8a4 4 0 1 1 3.5 6.5H14V11H10A6 6 0 1 0 4 8z" />
              <path d="M2 5h3V2z" />
            </svg>
          }
          label="撤销"
          disabled={!store.canUndo()}
          onClick={() => store.undo()}
          title="撤销 (Ctrl+Z)"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M12 8a4 4 0 1 0-3.5-6.5H2v3h6.5A6 6 0 1 1 12 8z" />
              <path d="M14 5h-3V2z" />
            </svg>
          }
          label="重做"
          disabled={!store.canRedo()}
          onClick={() => store.redo()}
          title="重做 (Ctrl+Y)"
        />
      </div>

      {/* Center section - Zoom controls */}
      <div className="flex items-center gap-2">
        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M7 3v10M3 7h10" stroke="currentColor" strokeWidth="2" />
            </svg>
          }
          label="放大"
          onClick={() => ui.zoomIn()}
          title="放大 (+)"
        />

        <span className="text-sm text-gray-400 min-w-[50px] text-center">
          {Math.round(ui.zoom * 100)}%
        </span>

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M3 7h10" stroke="currentColor" strokeWidth="2" />
            </svg>
          }
          label="缩小"
          onClick={() => ui.zoomOut()}
          title="缩小 (-)"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="7" cy="7" r="2" />
            </svg>
          }
          label="重置"
          onClick={() => ui.resetZoom()}
          title="重置视图 (0)"
        />

        <div className="w-px h-6 bg-schematic-accent mx-2" />

        {/* Grid controls */}
        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path
                d="M0 0v16M4 0v16M8 0v16M12 0v16M0 0h16M0 4h16M0 8h16M0 12h16"
                stroke="currentColor"
                strokeWidth="1"
                fill="none"
              />
            </svg>
          }
          label="网格"
          active={ui.gridVisible}
          onClick={() => ui.toggleGrid()}
          title="切换网格 (G)"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <circle cx="8" cy="8" r="2" />
              <path
                d="M8 2v2M8 12v2M2 8h2M12 8h2M3.5 3.5l1.5 1.5M11 11l1.5 1.5M3.5 12.5l1.5-1.5M11 5l1.5-1.5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          }
          label="吸附"
          active={ui.snapToGrid}
          onClick={() => ui.toggleSnap()}
          title="切换网格吸附 (S)"
        />

        {/* Grid size selector */}
        <select
          value={ui.gridSize}
          onChange={(e) => ui.setGridSize(parseInt(e.target.value))}
          className="bg-schematic-bg border border-schematic-accent rounded px-2 py-1 text-xs text-white"
          title="网格大小"
        >
          <option value={5}>5px</option>
          <option value={10}>10px</option>
          <option value={20}>20px</option>
          <option value={50}>50px</option>
        </select>
      </div>

      {/* Right section - Actions */}
      <div className="flex items-center gap-2">
        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zM6 5l5 3-5 3V5z" />
            </svg>
          }
          label="DRC"
          onClick={onRunDRC}
          title="运行设计规则检查"
          className="bg-yellow-600 hover:bg-yellow-700"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M2 3h12v2H2V3zm0 4h12v2H2V7zm0 4h8v2H2v-2z" />
            </svg>
          }
          label="全选"
          onClick={() =>
            ui.setSelectedComponents(store.components.map((c) => c.id))
          }
          title="全选 (Ctrl+A)"
        />

        <ToolButton
          icon={
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M5 2v12h8V2H5zM4 0h10v2H4V0zm0 3h10v1H4V3z" />
            </svg>
          }
          label="删除"
          onClick={() => {
            ui.selectedComponents.forEach((id) => {
              store.removeComponent(id);
            });
            ui.clearSelection();
          }}
          disabled={ui.selectedComponents.length === 0}
          title="删除选中 (Delete)"
          className="text-red-400 hover:text-red-300"
        />
      </div>
    </div>
  );
}

// Tool button component
interface ToolButtonProps {
  icon: React.ReactNode;
  label?: string;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  title?: string;
  className?: string;
}

function ToolButton({
  icon,
  label,
  active,
  disabled,
  onClick,
  title,
  className = '',
}: ToolButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`
        flex items-center gap-1 px-2 py-1.5 rounded text-xs transition-colors
        ${
          disabled
            ? 'opacity-40 cursor-not-allowed text-gray-500'
            : active
            ? 'bg-schematic-highlight text-white'
            : 'text-gray-400 hover:text-white hover:bg-schematic-accent/50 ' + className
        }
      `}
    >
      {icon}
      {label && <span>{label}</span>}
    </button>
  );
}
