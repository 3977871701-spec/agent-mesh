import React, { useRef, useState, useCallback, useEffect } from 'react';
import { useSchematicStore } from '../../store/schematicStore';
import { useUIStore } from '../../store/uiStore';
import { ComponentSymbols } from '../../assets/components/symbols';
import { ComponentType, Wire, WireDrawingState, Component } from '../../types';
import {
  findNearestPin,
  generateWirePath,
  generateWirePreviewPath,
  snapToGrid as snapToGridUtil,
  getPinAbsolutePosition,
  findJunctions,
  shouldShowJunction,
  distance,
} from '../../services/wireService';
import { findNetByPin, getNetHighlightColor } from '../../services/netService';

interface DragState {
  isDragging: boolean;
  componentId: string | null;
  startX: number;
  startY: number;
  offsetX: number;
  offsetY: number;
}

interface SelectionBox {
  active: boolean;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export default function CanvasEditor() {
  const svgRef = useRef<SVGSVGElement>(null);
  const store = useSchematicStore();
  const ui = useUIStore();

  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    componentId: null,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0,
  });

  const [selectionBox, setSelectionBox] = useState<SelectionBox>({
    active: false,
    startX: 0,
    startY: 0,
    endX: 0,
    endY: 0,
  });

  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Wire drawing state - use ref to avoid stale closure issues
  const [wireDrawing, setWireDrawing] = useState<WireDrawingState>({
    isDrawing: false,
    startPinId: null,
    startX: 0,
    startY: 0,
    waypoints: [],
    currentX: 0,
    currentY: 0,
  });

  // Ref to track current wireDrawing state for event handlers
  const wireDrawingRef = useRef(wireDrawing);
  useEffect(() => {
    wireDrawingRef.current = wireDrawing;
  }, [wireDrawing]);

  // Snap to grid helper
  const snapToGrid = useCallback(
    (value: number, gridSize: number, enabled: boolean): number => {
      return snapToGridUtil(value, gridSize, enabled);
    },
    []
  );

  // Get mouse position relative to SVG
  const getMousePosition = useCallback(
    (e: React.MouseEvent): { x: number; y: number } => {
      if (!svgRef.current) return { x: 0, y: 0 };
      const pt = svgRef.current.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const svgP = pt.matrixTransform(svgRef.current.getScreenCTM()?.inverse());
      return {
        x: (svgP.x - ui.panX) / ui.zoom,
        y: (svgP.y - ui.panY) / ui.zoom,
      };
    },
    [ui.panX, ui.panY, ui.zoom]
  );

  // Handle component mouse down for dragging
  const handleComponentMouseDown = useCallback(
    (e: React.MouseEvent, componentId: string) => {
      e.stopPropagation();

      if (ui.toolMode !== 'select') return;

      const pos = getMousePosition(e);
      const component = store.components.find((c) => c.id === componentId);

      if (!component) return;

      // Handle multi-select with Shift
      if (e.shiftKey) {
        ui.toggleSelection(componentId);
      } else if (!ui.selectedComponents.includes(componentId)) {
        // If clicking a non-selected component, select only it
        ui.setSelectedComponents([componentId]);
      }

      setDragState({
        isDragging: true,
        componentId,
        startX: component.x,
        startY: component.y,
        offsetX: pos.x - component.x,
        offsetY: pos.y - component.y,
      });
    },
    [getMousePosition, store.components, ui, ui.toolMode]
  );

  // Handle mouse move for dragging or panning
  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const pos = getMousePosition(e);
      const snappedX = snapToGrid(pos.x, ui.gridSize, ui.snapToGrid);
      const snappedY = snapToGrid(pos.y, ui.gridSize, ui.snapToGrid);

      if (isPanning) {
        ui.setPan(
          ui.panX + (e.clientX - panStart.x),
          ui.panY + (e.clientY - panStart.y)
        );
        setPanStart({ x: e.clientX, y: e.clientY });
        return;
      }

      // Update wire preview while drawing
      if (wireDrawingRef.current.isDrawing) {
        setWireDrawing((prev) => ({
          ...prev,
          currentX: snappedX,
          currentY: snappedY,
        }));
      }

      if (dragState.isDragging && dragState.componentId) {
        const newX = snapToGrid(pos.x - dragState.offsetX, ui.gridSize, ui.snapToGrid);
        const newY = snapToGrid(pos.y - dragState.offsetY, ui.gridSize, ui.snapToGrid);

        // Move all selected components
        const dx = newX - dragState.startX;
        const dy = newY - dragState.startY;

        ui.selectedComponents.forEach((id) => {
          const comp = store.components.find((c) => c.id === id);
          if (comp) {
            store.updateComponent(id, {
              x: snapToGrid(comp.x + dx - (dragState.startX - comp.x), ui.gridSize, ui.snapToGrid),
              y: snapToGrid(comp.y + dy - (dragState.startY - comp.y), ui.gridSize, ui.snapToGrid),
            });
          }
        });

        // Actually, let's simplify: move based on delta
        if (ui.selectedComponents.length === 1) {
          store.updateComponent(dragState.componentId, { x: newX, y: newY });
        }
      }

      if (selectionBox.active) {
        setSelectionBox((prev) => ({ ...prev, endX: pos.x, endY: pos.y }));
      }
    },
    [
      getMousePosition,
      isPanning,
      panStart,
      ui,
      dragState,
      selectionBox.active,
      snapToGrid,
      store,
    ]
  );

  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    if (selectionBox.active) {
      // Select components within the selection box
      const minX = Math.min(selectionBox.startX, selectionBox.endX);
      const maxX = Math.max(selectionBox.startX, selectionBox.endX);
      const minY = Math.min(selectionBox.startY, selectionBox.endY);
      const maxY = Math.max(selectionBox.startY, selectionBox.endY);

      const selectedInBox = store.components
        .filter((c) => c.x >= minX && c.x <= maxX && c.y >= minY && c.y <= maxY)
        .map((c) => c.id);

      if (selectedInBox.length > 0) {
        ui.setSelectedComponents(selectedInBox);
      }
    }

    setDragState({
      isDragging: false,
      componentId: null,
      startX: 0,
      startY: 0,
      offsetX: 0,
      offsetY: 0,
    });

    setSelectionBox((prev) => ({ ...prev, active: false }));
    setIsPanning(false);
  }, [selectionBox, store.components, ui]);

  // Handle canvas mouse down for selection box or panning
  const handleCanvasMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button === 1 || (e.button === 0 && e.altKey)) {
        // Middle mouse or Alt+Left click for panning
        setIsPanning(true);
        setPanStart({ x: e.clientX, y: e.clientY });
        return;
      }

      if (ui.toolMode === 'wire') {
        const pos = getMousePosition(e);
        const snappedX = snapToGrid(pos.x, ui.gridSize, ui.snapToGrid);
        const snappedY = snapToGrid(pos.y, ui.gridSize, ui.snapToGrid);

        // Check if clicking on a pin
        const pinHit = findNearestPin(pos.x, pos.y, store.components, undefined, 15);
        const currentWireDrawing = wireDrawingRef.current;

        if (!currentWireDrawing.isDrawing) {
          // Start new wire drawing
          if (pinHit) {
            // Start from pin
            setWireDrawing({
              isDrawing: true,
              startPinId: pinHit.pinId,
              startX: snappedX,
              startY: snappedY,
              waypoints: [snappedX, snappedY],
              currentX: snappedX,
              currentY: snappedY,
            });
          } else {
            // Start from empty canvas (free wire)
            setWireDrawing({
              isDrawing: true,
              startPinId: null,
              startX: snappedX,
              startY: snappedY,
              waypoints: [snappedX, snappedY],
              currentX: snappedX,
              currentY: snappedY,
            });
          }
        } else {
          // Continue drawing - add waypoint
          if (pinHit && pinHit.pinId !== currentWireDrawing.startPinId) {
            // Clicked on a different pin - finish wire
            finishWireDrawing(pinHit.pinId, snappedX, snappedY);
          } else if (!pinHit) {
            // Click on empty canvas - add waypoint
            setWireDrawing((prev) => ({
              ...prev,
              waypoints: [...prev.waypoints, snappedX, snappedY],
              currentX: snappedX,
              currentY: snappedY,
            }));
          }
        }
        return;
      }

      if (ui.toolMode === 'select') {
        const pos = getMousePosition(e);
        setSelectionBox({
          active: true,
          startX: pos.x,
          startY: pos.y,
          endX: pos.x,
          endY: pos.y,
        });
        // Clear selection when clicking on empty canvas
        if (!e.shiftKey) {
          ui.clearSelection();
        }
      }
    },
    [getMousePosition, ui, store]
  );

  // Handle wheel for zoom
  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      ui.setZoom(ui.zoom * delta);
    },
    [ui, ui.zoom]
  );

  // Handle double-click to end wire drawing
  const handleDoubleClick = useCallback(
    (_e: React.MouseEvent) => {
      if (ui.toolMode === 'wire' && wireDrawingRef.current.isDrawing) {
        const wd = wireDrawingRef.current;
        // End wire without connecting to a pin
        if (wd.waypoints.length >= 4) {
          const endX = wd.currentX;
          const endY = wd.currentY;
          const wire: Omit<Wire, 'id'> = {
            points: [...wd.waypoints, endX, endY],
          };
          store.addWire(wire);
        }
        setWireDrawing({
          isDrawing: false,
          startPinId: null,
          startX: 0,
          startY: 0,
          waypoints: [],
          currentX: 0,
          currentY: 0,
        });
      }
    },
    [ui.toolMode, store]
  );

  // Handle escape to cancel wire drawing
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && wireDrawingRef.current.isDrawing) {
        setWireDrawing({
          isDrawing: false,
          startPinId: null,
          startX: 0,
          startY: 0,
          waypoints: [],
          currentX: 0,
          currentY: 0,
        });
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Finish wire drawing and create wire + net
  const finishWireDrawing = useCallback(
    (endPinId: string, endX: number, endY: number) => {
      const wd = wireDrawingRef.current;
      if (wd.waypoints.length < 2) return;

      const wirePoints = [...wd.waypoints, endX, endY];
      const wire: Omit<Wire, 'id'> = { points: wirePoints };
      const wireId = store.addWire(wire);

      // Update nets - associate wire with connected nets
      const startPinId = wd.startPinId;
      const startNet = startPinId ? findNetByPin(store.nets, startPinId) : null;
      const endNet = findNetByPin(store.nets, endPinId);

      if (!startNet && !endNet) {
        // Create new net connecting both pins
        const netName = inferNetNameFromPins(startPinId, endPinId, store.components);
        store.addNet({
          name: netName,
          pins: [startPinId, endPinId].filter(Boolean) as string[],
          wires: [{ id: wireId, points: wirePoints }],
        });
      } else if (startNet && endNet && startNet.id !== endNet.id) {
        // Merge two nets - remove endNet, add its pins to startNet
        const mergedPins = [...new Set([...startNet.pins, ...endNet.pins])];
        const mergedWires = [
          ...startNet.wires,
          ...endNet.wires,
          { id: wireId, points: wirePoints },
        ];
        store.removeNet(endNet.id);
        store.removeNet(startNet.id);
        const newNetName = startNet.name || endNet.name || '';
        store.addNet({
          name: newNetName,
          pins: mergedPins,
          wires: mergedWires,
        });
      } else if (startNet) {
        store.removeNet(startNet.id);
        store.addNet({
          name: startNet.name,
          pins: [...startNet.pins, endPinId],
          wires: [...startNet.wires, { id: wireId, points: wirePoints }],
        });
      } else if (endNet) {
        store.removeNet(endNet.id);
        store.addNet({
          name: endNet.name,
          pins: [...endNet.pins, startPinId!],
          wires: [...endNet.wires, { id: wireId, points: wirePoints }],
        });
      }

      setWireDrawing({
        isDrawing: false,
        startPinId: null,
        startX: 0,
        startY: 0,
        waypoints: [],
        currentX: 0,
        currentY: 0,
      });
    },
    [store]
  );

  // Infer net name from connected pins
  const inferNetNameFromPins = (pinId1: string | null, pinId2: string, components: Component[]): string => {
    const pinIds = [pinId1, pinId2].filter(Boolean) as string[];
    for (const pinId of pinIds) {
      const [compId, localPinId] = pinId.split(':');
      const comp = components.find((c) => c.id === compId);
      if (!comp) continue;
      const pin = comp.pins.find((p) => p.id === localPinId);
      if (!pin) continue;

      const lowerName = (pin.name || '').toLowerCase();
      if (lowerName.includes('vcc') || lowerName.includes('power') || lowerName.includes('vdd')) {
        return 'VCC';
      }
      if (lowerName.includes('gnd') || lowerName.includes('ground')) {
        return 'GND';
      }
      if (comp.type === ComponentType.GND) return 'GND';
      if (comp.type === ComponentType.POWER) return 'VCC';
    }
    return '';
  };

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        // Delete selected components
        ui.selectedComponents.forEach((id) => {
          store.removeComponent(id);
        });
        ui.clearSelection();
      }

      if (e.key === 'Escape') {
        ui.clearSelection();
      }

      // Ctrl/Cmd + A for select all
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault();
        ui.setSelectedComponents(store.components.map((c) => c.id));
      }

      // Arrow keys for nudge
      if (ui.selectedComponents.length > 0) {
        const step = e.shiftKey ? ui.gridSize : 1;
        let dx = 0,
          dy = 0;
        if (e.key === 'ArrowLeft') dx = -step;
        if (e.key === 'ArrowRight') dx = step;
        if (e.key === 'ArrowUp') dy = -step;
        if (e.key === 'ArrowDown') dy = step;

        if (dx !== 0 || dy !== 0) {
          e.preventDefault();
          ui.selectedComponents.forEach((id) => {
            const comp = store.components.find((c) => c.id === id);
            if (comp) {
              store.updateComponent(id, {
                x: snapToGrid(comp.x + dx, ui.gridSize, ui.snapToGrid),
                y: snapToGrid(comp.y + dy, ui.gridSize, ui.snapToGrid),
              });
            }
          });
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [ui, store, snapToGrid]);

  // Get symbol component
  const getSymbolComponent = (type: ComponentType) => {
    return ComponentSymbols[type] || ComponentSymbols[ComponentType.GENERIC_IC];
  };

  // Debug: log wire count when component mounts or wires change
  console.log('CanvasEditor render - wires count:', store.wires.length);
  if (store.wires.length > 0) {
    console.log('Wire sample:', JSON.stringify(store.wires[0]));
  }

  // 计算导线交叉点（结点）
  const junctions = findJunctions(store.wires, 5);

  return (
    <div className="relative w-full" style={{ height: '500px' }}>
      <svg
        ref={svgRef}
        width="100%"
        height="500"
        viewBox="0 0 1000 500"
        preserveAspectRatio="xMidYMid meet"
        className="cursor-crosshair"
        style={{
          cursor:
            isPanning || ui.toolMode === 'pan'
              ? 'grab'
              : ui.toolMode === 'wire'
              ? 'crosshair'
              : 'default',
        }}
        onMouseDown={handleCanvasMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onDoubleClick={handleDoubleClick}
      >
        {/* Grid pattern definition - MUST be outside transform group */}
        <defs>
          <pattern
            id="editor-grid"
            width={ui.gridSize}
            height={ui.gridSize}
            patternUnits="userSpaceOnUse"
          >
            <path
              d={`M ${ui.gridSize} 0 L 0 0 0 ${ui.gridSize}`}
              fill="none"
              stroke="#2a2a4a"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>

        {/* Transform group for zoom and pan */}
        <g transform={`translate(${ui.panX}, ${ui.panY}) scale(${ui.zoom})`}>
          {/* Grid background */}
          <rect
            x="0"
            y="0"
            width="1000"
            height="500"
            fill={ui.gridVisible ? 'url(#editor-grid)' : 'transparent'}
          />

          {/* Wires */}
          {store.wires.length === 0 && (
            <text x="200" y="250" fill="orange" fontSize="14" fontFamily="monospace">暂无导线</text>
          )}
          {store.wires.map((wire) => {
            const pathData = generateWirePath(wire);
            if (!pathData) {
              console.warn('[WIRE] Empty path for wire:', wire.id, 'points:', wire.points);
              return null;
            }
            return (
              <path
                key={wire.id}
                d={pathData}
                stroke="#00ff88"
                strokeWidth="2"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            );
          })}

          {/* Junction points - 当多条导线相交时显示实心圆点 */}
          {junctions.filter(shouldShowJunction).map((junction, idx) => (
            <circle
              key={`junction-${idx}`}
              cx={junction.x}
              cy={junction.y}
              r="4"
              fill="#00ff88"
              stroke="#1a1a2e"
              strokeWidth="1"
            />
          ))}

          {/* Wire connection dots at component pins */}
          {store.components.map((comp) =>
            comp.pins.map((pin) => {
              const pinPos = getPinAbsolutePosition(comp, pin);
              const pinId = `${comp.id}:${pin.id}`;
              const net = findNetByPin(store.nets, pinId);
              const netColor = net && net.name ? getNetHighlightColor(net.name) : null;

              // 检查是否有导线连接到该引脚
              const hasConnection = store.wires.some((wire) => {
                const points = wire.points;
                for (let i = 0; i < points.length - 2; i += 2) {
                  const dist = distance(pinPos.x, pinPos.y, points[i], points[i + 1]);
                  if (dist < 5) return true;
                }
                // 检查终点
                const lastIdx = points.length - 2;
                const dist = distance(pinPos.x, pinPos.y, points[lastIdx], points[lastIdx + 1]);
                return dist < 5;
              });

              if (hasConnection) {
                return (
                  <circle
                    key={`pin-connection-${pinId}`}
                    cx={pinPos.x}
                    cy={pinPos.y}
                    r="5"
                    fill={netColor || '#6b7280'}
                    stroke="#1a1a2e"
                    strokeWidth="1"
                  />
                );
              }
              return null;
            })
          )}

          {/* Wire preview during drawing */}
          {wireDrawing.isDrawing && wireDrawing.waypoints.length >= 2 && (
            <>
              {/* Preview path */}
              <path
                d={generateWirePreviewPath(
                  wireDrawing.waypoints,
                  wireDrawing.currentX,
                  wireDrawing.currentY
                )}
                className="stroke-schematic-highlight stroke-2 fill-none stroke-dasharray-5-3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Waypoint markers */}
              {wireDrawing.waypoints.map((_, idx) => {
                if (idx % 2 !== 0) return null;
                const x = wireDrawing.waypoints[idx];
                const y = wireDrawing.waypoints[idx + 1];
                return (
                  <circle
                    key={idx}
                    cx={x}
                    cy={y}
                    r="4"
                    className="fill-schematic-highlight stroke-none"
                  />
                );
              })}
              {/* Current mouse position marker */}
              <circle
                cx={wireDrawing.currentX}
                cy={wireDrawing.currentY}
                r="4"
                className="fill-schematic-highlight stroke-white stroke-1"
              />
              {/* Pin hit indicator */}
              {(() => {
                const pinHit = findNearestPin(
                  wireDrawing.currentX,
                  wireDrawing.currentY,
                  store.components,
                  wireDrawing.startPinId || undefined,
                  15
                );
                if (pinHit) {
                  const absPos = getPinAbsolutePosition(pinHit.component, pinHit.pin);
                  return (
                    <circle
                      cx={absPos.x}
                      cy={absPos.y}
                      r="10"
                      className="fill-schematic-highlight fill-opacity-30 stroke-schematic-highlight stroke-2"
                    />
                  );
                }
                return null;
              })()}
            </>
          )}

          {/* Components */}
          {store.components.map((comp) => {
            const SymbolComponent = getSymbolComponent(comp.type);
            const isSelected =
              ui.selectedComponents.includes(comp.id) ||
              store.selectedComponent === comp.id;
            const isHovered = ui.hoveredComponent === comp.id;

            return (
              <g
                key={comp.id}
                transform={`translate(${comp.x}, ${comp.y}) rotate(${comp.rotation})`}
                className={`cursor-move transition-opacity ${
                  isHovered ? 'opacity-80' : ''
                }`}
                onMouseDown={(e) => handleComponentMouseDown(e, comp.id)}
                onMouseEnter={() => ui.setHoveredComponent(comp.id)}
                onMouseLeave={() => ui.setHoveredComponent(null)}
              >
                {/* Selection highlight */}
                {isSelected && (
                  <rect
                    x="-40"
                    y="-40"
                    width="80"
                    height="80"
                    fill="none"
                    stroke="#00ff88"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                    className="pointer-events-none"
                  />
                )}

                <SymbolComponent x={0} y={0} rotation={0} />

                {/* Labels */}
                <text
                  x="35"
                  y="-20"
                  className="fill-white text-xs font-bold select-none pointer-events-none"
                >
                  {comp.reference}
                </text>
                <text
                  x="35"
                  y="-8"
                  className="fill-gray-400 text-xs select-none pointer-events-none"
                >
                  {comp.value}
                </text>
              </g>
            );
          })}

          {/* Selection box */}
          {selectionBox.active && (
            <rect
              x={Math.min(selectionBox.startX, selectionBox.endX)}
              y={Math.min(selectionBox.startY, selectionBox.endY)}
              width={Math.abs(selectionBox.endX - selectionBox.startX)}
              height={Math.abs(selectionBox.endY - selectionBox.startY)}
              fill="rgba(0, 255, 136, 0.1)"
              stroke="#00ff88"
              strokeWidth="1"
              strokeDasharray="5,5"
              className="pointer-events-none"
            />
          )}

          {/* Violation markers */}
          {store.violations.map((v) => (
            <g key={v.id} className="pointer-events-none">
              <circle
                cx={v.location?.x || 0}
                cy={v.location?.y || 0}
                r="8"
                fill="rgba(255, 0, 0, 0.3)"
              />
              <text
                x={v.location?.x || 0}
                y={(v.location?.y || 0) + 4}
                textAnchor="middle"
                className="fill-red-500 text-sm font-bold"
              >
                !
              </text>
            </g>
          ))}
        </g>
      </svg>

      {/* Zoom indicator */}
      <div className="absolute bottom-4 right-4 bg-schematic-panel/80 backdrop-blur px-3 py-1 rounded text-sm text-gray-300">
        {Math.round(ui.zoom * 100)}%
      </div>

      {/* Selection info */}
      {ui.selectedComponents.length > 0 && (
        <div className="absolute top-4 left-4 bg-schematic-panel/80 backdrop-blur px-3 py-1 rounded text-sm">
          <span className="text-schematic-highlight font-medium">
            {ui.selectedComponents.length}
          </span>
          <span className="text-gray-400"> 个器件已选中</span>
        </div>
      )}
    </div>
  );
}
