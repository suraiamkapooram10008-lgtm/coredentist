// ============================================
// CoreDent PMS - Treatment Plan Visual Builder
// Interactive builder with tooth chart and DnD phases
// ============================================

import React, { useState, useMemo } from 'react';
import { 
  DndContext, 
  closestCenter, 
  KeyboardSensor, 
  PointerSensor, 
  useSensor, 
  useSensors,
  DragOverlay,
  type DragStartEvent,
  type DragOverEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { 
  arrayMove, 
  SortableContext, 
  sortableKeyboardCoordinates, 
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { 
  Search, 
  Plus, 
  GripVertical, 
  Trash2, 
  Info
} from 'lucide-react';
import { DentalChartView } from '../chart/DentalChartView';
import { ToothSVG } from '../chart/ToothSVG';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { 
  TreatmentProcedure, 
  ProcedurePhase, 
  TreatmentPlan 
} from '@/types/treatmentPlan';
import { 
  PHASE_CONFIG, 
  PROCEDURE_TEMPLATES,
  calculatePlanSummary 
} from '@/types/treatmentPlan';
import { cn } from '@/lib/utils';
import { v4 as uuidv4 } from 'uuid';

interface VisualBuilderProps {
  plan: TreatmentPlan;
  onUpdate: (updatedPlan: TreatmentPlan) => void;
  onCancel: () => void;
}

// --- Sortable Procedure Item ---
interface SortableProcedureProps {
  procedure: TreatmentProcedure;
  onDelete: (id: string) => void;
}

function SortableProcedure({ procedure, onDelete }: SortableProcedureProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: procedure.id });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
    zIndex: isDragging ? 50 : undefined,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="group">
      <Card className="hover:border-primary/50 transition-colors shadow-sm mb-2">
        <CardContent className="p-3 flex items-center gap-3">
          <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-primary">
            <GripVertical className="h-4 w-4" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-[10px] px-1.5 h-4 border-primary/20 bg-primary/5">
                {procedure.procedureCode}
              </Badge>
              {procedure.toothNumber && (
                <Badge variant="secondary" className="text-[10px] px-1.5 h-4 bg-muted">
                   T#{procedure.toothNumber}
                </Badge>
              )}
            </div>
            <p className="text-sm font-medium leading-none mt-1.5 truncate">
              {procedure.procedureName}
            </p>
          </div>

          <div className="text-right">
            <p className="text-sm font-semibold">${procedure.estimatedCost}</p>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={() => onDelete(procedure.id)}
            >
              <Trash2 className="h-3.5 w-3.5 text-destructive" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// --- Droppable Phase Container ---
interface PhaseContainerProps {
  id: ProcedurePhase;
  procedures: TreatmentProcedure[];
  onDeleteProcedure: (id: string) => void;
}

function PhaseContainer({ id, procedures, onDeleteProcedure }: PhaseContainerProps) {
  const config = PHASE_CONFIG[id];
  const { setNodeRef } = useSortable({ id });

  return (
    <div className="flex flex-col h-full bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
      <div className={cn("p-3 rounded-t-xl flex justify-between items-center", config.color)}>
        <h3 className="font-bold text-sm">{config.label}</h3>
        <Badge variant="secondary" className="bg-white/50 text-[10px]">
          {procedures.length} Items
        </Badge>
      </div>
      
      <ScrollArea className="flex-1 p-3 min-h-[150px]">
        <div ref={setNodeRef}>
          <SortableContext items={procedures.map(p => p.id)} strategy={verticalListSortingStrategy}>
            {procedures.map(proc => (
              <SortableProcedure 
                key={proc.id} 
                procedure={proc} 
                onDelete={onDeleteProcedure} 
              />
            ))}
          </SortableContext>
          {procedures.length === 0 && (
            <div className="h-32 flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed border-slate-200 rounded-lg">
              <Plus className="h-5 w-5 mb-1 opacity-20" />
              <p className="text-[10px] text-center px-4">Drag procedures here</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

export function TreatmentPlanVisualBuilder({ plan, onUpdate, onCancel }: VisualBuilderProps) {
  const [procedures, setProcedures] = useState<TreatmentProcedure[]>(plan.procedures);
  const [selectedTooth, setSelectedTooth] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeId, setActiveId] = useState<string | null>(null);

  // DnD Sensors
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const summary = useMemo(() => calculatePlanSummary({ ...plan, procedures }), [plan, procedures]);

  // Handle Drag Events
  const handleDragStart = ({ active }: DragStartEvent) => {
    setActiveId(active.id as string);
  };

  const handleDragOver = ({ active, over }: DragOverEvent) => {
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Is it a phase or a procedure?
    const activeProc = procedures.find(p => p.id === activeId);
    if (!activeProc) return;

    const overIsPhase = Object.keys(PHASE_CONFIG).includes(overId);
    const overProc = procedures.find(p => p.id === overId);

    if (overIsPhase) {
      if (activeProc.phase !== overId) {
        setProcedures(prev => prev.map(p => p.id === activeId ? { ...p, phase: overId as ProcedurePhase } : p));
      }
    } else if (overProc && activeProc.phase !== overProc.phase) {
      setProcedures(prev => prev.map(p => p.id === activeId ? { ...p, phase: overProc.phase } : p));
    }
  };

  const handleDragEnd = ({ active, over }: DragEndEvent) => {
    if (over && active.id !== over.id) {
      const activeIndex = procedures.findIndex(p => p.id === active.id);
      const overIndex = procedures.findIndex(p => p.id === over.id);
      
      if (activeIndex !== -1 && overIndex !== -1) {
        setProcedures((items) => arrayMove(items, activeIndex, overIndex));
      }
    }
    setActiveId(null);
  };

  // Logic: Add new procedure
  const handleAddProcedure = (template: typeof PROCEDURE_TEMPLATES[0]) => {
    const newProc: TreatmentProcedure = {
      id: uuidv4(),
      procedureCode: template.code,
      procedureName: template.name,
      toothNumber: selectedTooth || undefined,
      phase: 'phase_1',
      status: 'planned',
      estimatedCost: template.defaultCost,
      dentistId: 'demo-dentist',
      dentistName: 'Dr. Visual Builder',
    };
    setProcedures(prev => [...prev, newProc]);
  };

  const handleDeleteProcedure = (id: string) => {
    setProcedures(prev => prev.filter(p => p.id !== id));
  };

  const handleSave = () => {
    onUpdate({ ...plan, procedures, updatedAt: new Date().toISOString() });
  };

  const filteredTemplates = PROCEDURE_TEMPLATES.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    t.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full gap-4 max-h-[85vh]">
      {/* Top Section: Chart & Lib */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0 flex-1 overflow-hidden">
        
        {/* Left: Interactive Dental Chart (7 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <Card className="flex-1 border-none shadow-none bg-slate-50/20">
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-4 border-b">
                <h2 className="font-bold text-lg flex items-center gap-2">
                  <Badge variant="outline" className="rounded-full h-6 w-6 flex items-center justify-center p-0 bg-primary text-primary-foreground border-primary">1</Badge>
                  Select Target Tooth
                </h2>
                {selectedTooth ? (
                  <Badge variant="secondary" className="gap-1 animate-in fade-in slide-in-from-right-2 bg-primary/10 text-primary border-primary/20">
                    Selected Tooth #{selectedTooth}
                    <Button variant="ghost" size="icon" className="h-4 w-4 p-0 hover:bg-transparent" onClick={() => setSelectedTooth(null)}>
                      <Plus className="h-3 w-3 rotate-45" />
                    </Button>
                  </Badge>
                ) : (
                  <span className="text-xs text-muted-foreground italic">Click a tooth to associate it with a procedure</span>
                )}
              </div>
              <ScrollArea className="h-[250px] lg:h-[300px]">
                <div className="p-8 flex justify-center">
                  <DentalChartView 
                    teeth={new Array(32).fill(0).map((_, i) => ({ number: i + 1, status: 'healthy' }))}
                    selectedTooth={selectedTooth}
                    onSelectTooth={setSelectedTooth}
                  />
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Bottom Summary / Stats */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="bg-primary/5 border-primary/20">
              <CardContent className="p-4 flex flex-col items-center">
                <span className="text-[10px] font-bold text-primary tracking-wider uppercase">Total Cost</span>
                <span className="text-2xl font-black text-primary">${summary.totalEstimatedCost}</span>
              </CardContent>
            </Card>
            <Card className="bg-green-50/50 border-green-200">
              <CardContent className="p-4 flex flex-col items-center text-green-700">
                <span className="text-[10px] font-bold tracking-wider uppercase">Procedures</span>
                <span className="text-2xl font-black">{summary.totalProcedures}</span>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 flex flex-col items-center">
                <span className="text-[10px] font-bold text-muted-foreground tracking-wider uppercase">Status</span>
                <Badge variant="outline" className="mt-1">Proposed</Badge>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right: Procedure Library (4 cols) */}
        <Card className="lg:col-span-4 flex flex-col overflow-hidden border-l border-none shadow-none bg-white">
          <div className="p-4 border-b">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Badge variant="outline" className="rounded-full h-6 w-6 flex items-center justify-center p-0 bg-primary text-primary-foreground border-primary">2</Badge>
              Proc Library
            </h2>
            <div className="relative mt-3">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search codes or names..." 
                className="pl-9 h-9 text-sm"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 grid gap-1">
              {filteredTemplates.map(template => (
                <div 
                  key={template.code}
                  className="group flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 cursor-pointer border border-transparent hover:border-slate-200 transition-all font-inter"
                  onClick={() => handleAddProcedure(template)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <code className="text-[10px] font-bold text-primary bg-primary/10 px-1 rounded">{template.code}</code>
                      <span className="text-sm font-semibold truncate">{template.name}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-2">
                    <span className="text-sm font-bold">${template.defaultCost}</span>
                    <Button size="icon" variant="secondary" className="h-6 w-6 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </Card>
      </div>

      <Separator />

      {/* Bottom Section: Phases (DnD) */}
      <div className="h-[350px] flex flex-col gap-3">
        <h2 className="font-bold text-lg flex items-center gap-2">
          <Badge variant="outline" className="rounded-full h-6 w-6 flex items-center justify-center p-0 bg-primary text-primary-foreground border-primary">3</Badge>
          Timeline & Sequencing
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground ml-1" />
              </TooltipTrigger>
              <TooltipContent>
                Drag and drop procedures between phases to organize the patient's journey.
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </h2>
        
        <DndContext 
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 flex-1 h-[300px]">
             {(Object.keys(PHASE_CONFIG) as ProcedurePhase[]).map(phaseId => (
               <PhaseContainer 
                 key={phaseId} 
                 id={phaseId} 
                 procedures={procedures.filter(p => p.phase === phaseId)}
                 onDeleteProcedure={handleDeleteProcedure}
               />
             ))}
          </div>
          
          <DragOverlay>
            {activeId ? (
              <div className="shadow-2xl rotation-2 border-2 border-primary rounded-xl overflow-hidden bg-white scale-105 pointer-events-none">
                 <div className="p-4 bg-primary text-white text-sm font-bold">
                    Dragging Procedure...
                 </div>
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Footer Actions */}
      <div className="flex justify-end gap-3 pt-4 mt-auto border-t">
        <Button variant="ghost" onClick={onCancel}>Discard Changes</Button>
        <Button size="lg" className="px-10" onClick={handleSave}>
          Finalize Treatment Plan
        </Button>
      </div>
    </div>
  );
}
