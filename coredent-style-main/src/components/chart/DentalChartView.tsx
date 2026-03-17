// ============================================
// CoreDent PMS - Full Dental Chart View
// Interactive chart showing all 32 adult teeth
// ============================================

import React from 'react';
import { ToothSVG } from './ToothSVG';
import type { ToothData } from '@/types/dentalChart';

interface DentalChartViewProps {
  teeth: ToothData[];
  selectedTooth: number | null;
  onSelectTooth: (toothNumber: number) => void;
}

export function DentalChartView({ teeth, selectedTooth, onSelectTooth }: DentalChartViewProps) {
  // Upper teeth (1-16, displayed right to left for proper anatomical view)
  const upperTeeth = teeth.filter(t => t.number >= 1 && t.number <= 16);
  // Lower teeth (17-32, displayed left to right)
  const lowerTeeth = teeth.filter(t => t.number >= 17 && t.number <= 32);
  
  // Sort for proper display (patient's view - right side of mouth on left of screen)
  const upperRow = [...upperTeeth].sort((a, b) => a.number - b.number);
  const lowerRow = [...lowerTeeth].sort((a, b) => a.number - b.number);

  return (
    <div className="w-full">
      {/* Chart container */}
      <div className="bg-card border rounded-xl p-6 space-y-2">
        {/* Quadrant labels */}
        <div className="flex justify-between text-xs text-muted-foreground font-medium px-4">
          <span>Upper Right (Q1)</span>
          <span>Upper Left (Q2)</span>
        </div>
        
        {/* Upper arch - teeth 1-16 */}
        <div className="flex justify-center gap-1 pb-4 border-b-2 border-dashed border-muted">
          {upperRow.map(tooth => (
            <ToothSVG
              key={tooth.number}
              tooth={tooth}
              isSelected={selectedTooth === tooth.number}
              onClick={onSelectTooth}
              size={44}
            />
          ))}
        </div>
        
        {/* Center line indicator */}
        <div className="relative h-4">
          <div className="absolute left-1/2 -translate-x-1/2 top-0 flex flex-col items-center">
            <div className="w-px h-4 bg-muted-foreground/30" />
            <span className="text-[10px] text-muted-foreground">Midline</span>
          </div>
        </div>
        
        {/* Lower arch - teeth 17-32 */}
        <div className="flex justify-center gap-1 pt-4 border-t-2 border-dashed border-muted">
          {lowerRow.map(tooth => (
            <ToothSVG
              key={tooth.number}
              tooth={tooth}
              isSelected={selectedTooth === tooth.number}
              onClick={onSelectTooth}
              size={44}
            />
          ))}
        </div>
        
        {/* Quadrant labels */}
        <div className="flex justify-between text-xs text-muted-foreground font-medium px-4">
          <span>Lower Left (Q3)</span>
          <span>Lower Right (Q4)</span>
        </div>
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 justify-center text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-white border rounded" />
          <span className="text-muted-foreground">Healthy</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-200 border rounded" />
          <span className="text-muted-foreground">Decay</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-purple-200 border rounded" />
          <span className="text-muted-foreground">Filling</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-amber-200 border rounded" />
          <span className="text-muted-foreground">Crown</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-200 border rounded" />
          <span className="text-muted-foreground">Root Canal</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-cyan-200 border rounded" />
          <span className="text-muted-foreground">Implant</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-muted border rounded relative">
            <span className="absolute inset-0 flex items-center justify-center text-muted-foreground">×</span>
          </div>
          <span className="text-muted-foreground">Missing</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-500 rounded-full" />
          <span className="text-muted-foreground">Planned</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full" />
          <span className="text-muted-foreground">Completed</span>
        </div>
      </div>
    </div>
  );
}
