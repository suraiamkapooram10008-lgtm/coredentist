// ============================================
// CoreDent PMS - Individual Tooth SVG Component
// Renders a single interactive tooth with surfaces
// ============================================

import React from 'react';
import { cn } from '@/lib/utils';
import type { ToothData, ToothCondition } from '@/types/dentalChart';

interface ToothSVGProps {
  tooth: ToothData;
  isSelected: boolean;
  onClick: (toothNumber: number) => void;
  size?: number;
}

// Get fill color based on tooth condition
function getConditionFill(condition: ToothCondition): string {
  switch (condition) {
    case 'healthy':
      return 'fill-white';
    case 'decay':
      return 'fill-red-200';
    case 'filling':
      return 'fill-purple-200';
    case 'crown':
      return 'fill-amber-200';
    case 'root_canal':
      return 'fill-orange-200';
    case 'extraction':
    case 'missing':
      return 'fill-muted';
    case 'implant':
      return 'fill-cyan-200';
    case 'bridge':
      return 'fill-amber-100';
    case 'veneer':
      return 'fill-violet-100';
    default:
      return 'fill-white';
  }
}

// Check if tooth is a molar (has 5-surface display)
function isMolar(toothNumber: number): boolean {
  return [1, 2, 3, 14, 15, 16, 17, 18, 19, 30, 31, 32].includes(toothNumber);
}

// Check if tooth is anterior (incisors/canines - has 4 surfaces)
function isAnterior(toothNumber: number): boolean {
  return [6, 7, 8, 9, 10, 11, 22, 23, 24, 25, 26, 27].includes(toothNumber);
}

export function ToothSVG({ tooth, isSelected, onClick, size = 48 }: ToothSVGProps) {
  const conditionClass = getConditionFill(tooth.condition);
  const hasProcedures = tooth.procedures.length > 0;
  const hasPlannedProcedures = tooth.procedures.some(p => p.status === 'planned');
  const hasCompletedProcedures = tooth.procedures.some(p => p.status === 'completed');
  
  const isMissing = tooth.condition === 'missing' || tooth.condition === 'extraction';

  return (
    <div
      className={cn(
        'relative cursor-pointer transition-all duration-150 group',
        isSelected && 'scale-110 z-10'
      )}
      onClick={() => onClick(tooth.number)}
    >
      <svg
        width={size}
        height={size + 16}
        viewBox="0 0 48 64"
        className="overflow-visible"
      >
        {/* Tooth number */}
        <text
          x="24"
          y="10"
          textAnchor="middle"
          className="fill-muted-foreground text-[10px] font-medium"
        >
          {tooth.number}
        </text>
        
        {/* Tooth body */}
        <g transform="translate(4, 14)">
          {isMissing ? (
            // Missing tooth - X mark
            <g>
              <rect
                x="4"
                y="4"
                width="32"
                height="40"
                rx="4"
                className="fill-muted stroke-muted-foreground/30"
                strokeWidth="1"
              />
              <line
                x1="10"
                y1="12"
                x2="30"
                y2="36"
                className="stroke-muted-foreground/50"
                strokeWidth="2"
              />
              <line
                x1="30"
                y1="12"
                x2="10"
                y2="36"
                className="stroke-muted-foreground/50"
                strokeWidth="2"
              />
            </g>
          ) : isMolar(tooth.number) ? (
            // Molar - 5 surfaces (cross pattern)
            <g>
              {/* Outer border */}
              <rect
                x="4"
                y="4"
                width="32"
                height="40"
                rx="4"
                className={cn(
                  conditionClass,
                  'stroke-border transition-colors',
                  isSelected ? 'stroke-primary stroke-2' : 'stroke-1',
                  'group-hover:stroke-primary/50'
                )}
              />
              {/* Cross dividers */}
              <line x1="20" y1="4" x2="20" y2="44" className="stroke-border" strokeWidth="1" />
              <line x1="4" y1="24" x2="36" y2="24" className="stroke-border" strokeWidth="1" />
              {/* Center surface (occlusal) */}
              <rect
                x="12"
                y="16"
                width="16"
                height="16"
                rx="2"
                className={cn(
                  conditionClass,
                  'stroke-border'
                )}
                strokeWidth="1"
              />
            </g>
          ) : isAnterior(tooth.number) ? (
            // Anterior - 4 surfaces (diamond pattern)
            <g>
              <rect
                x="8"
                y="4"
                width="24"
                height="40"
                rx="12"
                className={cn(
                  conditionClass,
                  'stroke-border transition-colors',
                  isSelected ? 'stroke-primary stroke-2' : 'stroke-1',
                  'group-hover:stroke-primary/50'
                )}
              />
              {/* Incisal edge line */}
              <line x1="12" y1="12" x2="28" y2="12" className="stroke-border" strokeWidth="1" />
            </g>
          ) : (
            // Premolar - simplified molar
            <g>
              <rect
                x="6"
                y="4"
                width="28"
                height="40"
                rx="6"
                className={cn(
                  conditionClass,
                  'stroke-border transition-colors',
                  isSelected ? 'stroke-primary stroke-2' : 'stroke-1',
                  'group-hover:stroke-primary/50'
                )}
              />
              {/* Cross dividers */}
              <line x1="20" y1="8" x2="20" y2="40" className="stroke-border" strokeWidth="1" />
              <line x1="10" y1="24" x2="30" y2="24" className="stroke-border" strokeWidth="1" />
            </g>
          )}
        </g>
        
        {/* Procedure indicators */}
        {hasProcedures && !isMissing && (
          <g>
            {hasPlannedProcedures && (
              <circle
                cx="38"
                cy="18"
                r="5"
                className="fill-blue-500 stroke-white"
                strokeWidth="1"
              />
            )}
            {hasCompletedProcedures && (
              <circle
                cx={hasPlannedProcedures ? "38" : "38"}
                cy={hasPlannedProcedures ? "30" : "18"}
                r="5"
                className="fill-green-500 stroke-white"
                strokeWidth="1"
              />
            )}
          </g>
        )}
      </svg>
    </div>
  );
}
