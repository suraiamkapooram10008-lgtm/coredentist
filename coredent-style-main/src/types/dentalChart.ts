// ============================================
// CoreDent PMS - Dental Chart Types
// Types for dental charting and tooth procedures
// ============================================

export type ToothSurface = 'mesial' | 'distal' | 'occlusal' | 'buccal' | 'lingual' | 'facial' | 'incisal';

export type ProcedureStatus = 'planned' | 'in_progress' | 'completed';

export type ToothCondition = 
  | 'healthy'
  | 'decay'
  | 'filling'
  | 'crown'
  | 'root_canal'
  | 'extraction'
  | 'missing'
  | 'implant'
  | 'bridge'
  | 'veneer';

export interface ToothProcedure {
  id: string;
  toothNumber: number;
  surfaces: ToothSurface[];
  procedureCode: string;
  procedureName: string;
  status: ProcedureStatus;
  date: string;
  dentistId: string;
  dentistName: string;
  notes?: string;
  color: string;
}

export interface ToothData {
  number: number;
  name: string;
  quadrant: 1 | 2 | 3 | 4;
  isAdult: boolean;
  condition: ToothCondition;
  procedures: ToothProcedure[];
  notes?: string;
}

export interface DentalChart {
  patientId: string;
  patientName: string;
  teeth: ToothData[];
  lastUpdated: string;
}

// Universal Numbering System (US) - Adult teeth 1-32
export const ADULT_TEETH: { number: number; name: string; quadrant: 1 | 2 | 3 | 4 }[] = [
  // Upper Right (Quadrant 1) - 1-8
  { number: 1, name: 'Upper Right Third Molar', quadrant: 1 },
  { number: 2, name: 'Upper Right Second Molar', quadrant: 1 },
  { number: 3, name: 'Upper Right First Molar', quadrant: 1 },
  { number: 4, name: 'Upper Right Second Premolar', quadrant: 1 },
  { number: 5, name: 'Upper Right First Premolar', quadrant: 1 },
  { number: 6, name: 'Upper Right Canine', quadrant: 1 },
  { number: 7, name: 'Upper Right Lateral Incisor', quadrant: 1 },
  { number: 8, name: 'Upper Right Central Incisor', quadrant: 1 },
  // Upper Left (Quadrant 2) - 9-16
  { number: 9, name: 'Upper Left Central Incisor', quadrant: 2 },
  { number: 10, name: 'Upper Left Lateral Incisor', quadrant: 2 },
  { number: 11, name: 'Upper Left Canine', quadrant: 2 },
  { number: 12, name: 'Upper Left First Premolar', quadrant: 2 },
  { number: 13, name: 'Upper Left Second Premolar', quadrant: 2 },
  { number: 14, name: 'Upper Left First Molar', quadrant: 2 },
  { number: 15, name: 'Upper Left Second Molar', quadrant: 2 },
  { number: 16, name: 'Upper Left Third Molar', quadrant: 2 },
  // Lower Left (Quadrant 3) - 17-24
  { number: 17, name: 'Lower Left Third Molar', quadrant: 3 },
  { number: 18, name: 'Lower Left Second Molar', quadrant: 3 },
  { number: 19, name: 'Lower Left First Molar', quadrant: 3 },
  { number: 20, name: 'Lower Left Second Premolar', quadrant: 3 },
  { number: 21, name: 'Lower Left First Premolar', quadrant: 3 },
  { number: 22, name: 'Lower Left Canine', quadrant: 3 },
  { number: 23, name: 'Lower Left Lateral Incisor', quadrant: 3 },
  { number: 24, name: 'Lower Left Central Incisor', quadrant: 3 },
  // Lower Right (Quadrant 4) - 25-32
  { number: 25, name: 'Lower Right Central Incisor', quadrant: 4 },
  { number: 26, name: 'Lower Right Lateral Incisor', quadrant: 4 },
  { number: 27, name: 'Lower Right Canine', quadrant: 4 },
  { number: 28, name: 'Lower Right First Premolar', quadrant: 4 },
  { number: 29, name: 'Lower Right Second Premolar', quadrant: 4 },
  { number: 30, name: 'Lower Right First Molar', quadrant: 4 },
  { number: 31, name: 'Lower Right Second Molar', quadrant: 4 },
  { number: 32, name: 'Lower Right Third Molar', quadrant: 4 },
];

// Common dental procedure codes with colors
export const PROCEDURE_CODES: { code: string; name: string; color: string }[] = [
  { code: 'D0120', name: 'Periodic Oral Evaluation', color: '#22c55e' },
  { code: 'D0150', name: 'Comprehensive Oral Evaluation', color: '#22c55e' },
  { code: 'D1110', name: 'Prophylaxis (Cleaning)', color: '#3b82f6' },
  { code: 'D2140', name: 'Amalgam Filling - 1 Surface', color: '#8b5cf6' },
  { code: 'D2150', name: 'Amalgam Filling - 2 Surfaces', color: '#8b5cf6' },
  { code: 'D2330', name: 'Composite Filling - 1 Surface', color: '#a855f7' },
  { code: 'D2331', name: 'Composite Filling - 2 Surfaces', color: '#a855f7' },
  { code: 'D2740', name: 'Crown - Porcelain', color: '#f59e0b' },
  { code: 'D2750', name: 'Crown - Metal', color: '#f59e0b' },
  { code: 'D3310', name: 'Root Canal - Anterior', color: '#ef4444' },
  { code: 'D3320', name: 'Root Canal - Premolar', color: '#ef4444' },
  { code: 'D3330', name: 'Root Canal - Molar', color: '#ef4444' },
  { code: 'D4341', name: 'Periodontal Scaling', color: '#06b6d4' },
  { code: 'D7140', name: 'Extraction - Simple', color: '#64748b' },
  { code: 'D7210', name: 'Extraction - Surgical', color: '#64748b' },
  { code: 'D6010', name: 'Implant - Endosteal', color: '#ec4899' },
];

export const CONDITION_COLORS: Record<ToothCondition, string> = {
  healthy: 'hsl(var(--chart-2))',
  decay: 'hsl(var(--destructive))',
  filling: 'hsl(var(--chart-4))',
  crown: 'hsl(var(--chart-5))',
  root_canal: 'hsl(var(--chart-1))',
  extraction: 'hsl(var(--muted-foreground))',
  missing: 'hsl(var(--muted))',
  implant: 'hsl(var(--chart-3))',
  bridge: 'hsl(var(--chart-5))',
  veneer: 'hsl(var(--chart-4))',
};

export const STATUS_STYLES: Record<ProcedureStatus, { bg: string; text: string; border: string }> = {
  planned: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
  in_progress: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300' },
  completed: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
};
