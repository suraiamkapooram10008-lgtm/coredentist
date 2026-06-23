import { useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { calculatePlanSummary } from '@/types/treatmentPlan';
import type { TreatmentPlan, ProcedurePhase } from '@/types/treatmentPlan';
import { Plus, Check, Trash2, FileText, Loader2 } from 'lucide-react';

interface TreatmentPlanDetailsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan: TreatmentPlan | null;
  onAddProcedure: (data: {
    procedureCode: string;
    procedureName: string;
    toothNumber?: number;
    phase: ProcedurePhase;
    estimatedCost: number;
    notes?: string;
  }) => Promise<void>;
  onCompleteProcedure: (procedureId: string) => Promise<void>;
  onDeleteProcedure: (procedureId: string) => Promise<void>;
}

export function TreatmentPlanDetails({
  open,
  onOpenChange,
  plan,
  onAddProcedure,
  onCompleteProcedure,
  onDeleteProcedure,
}: TreatmentPlanDetailsProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form states for inline add
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [tooth, setTooth] = useState('');
  const [phase, setPhase] = useState<ProcedurePhase>('phase_1');
  const [cost, setCost] = useState('');
  const [notes, setNotes] = useState('');

  if (!plan) return null;

  const summary = calculatePlanSummary(plan);

  const handleAddProc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !name || !cost) return;
    setIsSubmitting(true);
    try {
      await onAddProcedure({
        procedureCode: code,
        procedureName: name,
        toothNumber: tooth ? parseInt(tooth) : undefined,
        phase,
        estimatedCost: parseFloat(cost),
        notes: notes.trim() || undefined,
      });
      // Reset
      setCode('');
      setName('');
      setTooth('');
      setCost('');
      setNotes('');
      setIsAdding(false);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getPhaseLabel = (ph: string) => {
    switch (ph) {
      case 'phase_1':
        return 'Phase 1: Urgent & Diagnostic';
      case 'phase_2':
        return 'Phase 2: Preventive & Hygiene';
      case 'phase_3':
        return 'Phase 3: Restorative & Surgical';
      case 'phase_4':
        return 'Phase 4: Cosmetic & Maintenance';
      default:
        return 'General Phase';
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[650px] overflow-y-auto custom-scrollbar p-8">
        <SheetHeader className="pb-4 border-b border-slate-100">
          <div className="flex justify-between items-start">
            <div>
              <SheetTitle className="text-2xl font-black text-slate-800 tracking-tight">{plan.title}</SheetTitle>
              <SheetDescription className="font-bold text-slate-400 text-xs mt-0.5">
                Patient Portal Code: {plan.patientName}
              </SheetDescription>
            </div>
            <Badge variant="outline" className="font-black uppercase tracking-wider text-[9px] bg-slate-50 text-slate-500 border-none capitalize px-3 py-1">
              {plan.status}
            </Badge>
          </div>
        </SheetHeader>

        <div className="py-6 space-y-6">
          {/* Quick Stats Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50/50 rounded-2xl p-4 text-center border border-slate-50">
            <div>
              <span className="text-[9px] font-black uppercase text-slate-400 tracking-widest">Total Plan</span>
              <p className="font-black text-slate-800 text-sm mt-0.5">${summary.totalEstimatedCost.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-[9px] font-black uppercase text-slate-400 tracking-widest">Insurance Est.</span>
              <p className="font-black text-emerald-600 text-sm mt-0.5">${summary.totalInsuranceEstimate.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-[9px] font-black uppercase text-slate-400 tracking-widest">Patient Net</span>
              <p className="font-black text-blue-600 text-sm mt-0.5">${summary.totalPatientResponsibility.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-[9px] font-black uppercase text-slate-400 tracking-widest">Done</span>
              <p className="font-black text-slate-700 text-sm mt-0.5">${summary.totalCompleted.toLocaleString()}</p>
            </div>
          </div>

          {/* Procedures List */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-black text-slate-800 tracking-tight uppercase tracking-widest text-slate-400 text-[10px]">Plan Procedures</h3>
              <Button
                size="sm"
                onClick={() => setIsAdding(!isAdding)}
                className="h-8 rounded-lg font-bold bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-1 text-[11px]"
              >
                <Plus className="w-3.5 h-3.5" /> Inline Add
              </Button>
            </div>

            {/* Inline Add Form */}
            {isAdding && (
              <form onSubmit={handleAddProc} className="p-4 border border-blue-100 rounded-2xl bg-blue-50/20 space-y-4 animate-in slide-in-from-top-2 duration-300">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-0.5">Code</Label>
                    <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="e.g. D2391" className="h-9 rounded-lg" required />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-0.5">Tooth #</Label>
                    <Input value={tooth} onChange={(e) => setTooth(e.target.value)} type="number" placeholder="e.g. 14" className="h-9 rounded-lg" />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-0.5">Procedure Name</Label>
                  <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Resin Composite - 1 Surface" className="h-9 rounded-lg" required />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-0.5">Phase</Label>
                    <Select value={phase} onValueChange={(val: any) => setPhase(val)}>
                      <SelectTrigger className="h-9 rounded-lg">
                        <SelectValue placeholder="Select phase" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="phase_1">Phase 1</SelectItem>
                        <SelectItem value="phase_2">Phase 2</SelectItem>
                        <SelectItem value="phase_3">Phase 3</SelectItem>
                        <SelectItem value="phase_4">Phase 4</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-0.5">Cost ($)</Label>
                    <Input value={cost} onChange={(e) => setCost(e.target.value)} type="number" placeholder="180" className="h-9 rounded-lg" required />
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" size="sm" variant="outline" onClick={() => setIsAdding(false)} className="rounded-lg h-9">
                    Cancel
                  </Button>
                  <Button type="submit" size="sm" disabled={isSubmitting} className="rounded-lg h-9 bg-blue-600 hover:bg-blue-700 text-white font-bold">
                    {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Log Procedure'}
                  </Button>
                </div>
              </form>
            )}

            {/* List Procedures by Phase */}
            {plan.procedures.length === 0 ? (
              <p className="text-xs text-slate-400 font-medium py-8 text-center bg-slate-50/50 rounded-2xl border border-dashed border-slate-100">
                No procedures mapped to this treatment plan.
              </p>
            ) : (
              (['phase_1', 'phase_2', 'phase_3', 'phase_4'] as ProcedurePhase[]).map((ph) => {
                const phaseProcs = plan.procedures.filter((p) => p.phase === ph);
                if (phaseProcs.length === 0) return null;
                return (
                  <div key={ph} className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-700 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100/50">
                      {getPhaseLabel(ph)}
                    </h4>
                    <div className="space-y-2 pl-1">
                      {phaseProcs.map((proc) => (
                        <div key={proc.id} className="p-3 border border-slate-50 rounded-xl hover:border-slate-200 transition-colors flex items-center justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${proc.status === 'completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-500'}`}>
                              {proc.status === 'completed' ? <Check className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                            </div>
                            <div>
                              <p className="text-xs font-bold text-slate-800">
                                {proc.procedureCode} — {proc.procedureName}
                                {proc.toothNumber && <span className="text-[10px] text-blue-500 font-bold ml-1.5">Tooth #{proc.toothNumber}</span>}
                              </p>
                              <p className="text-[10px] text-slate-400 font-medium flex items-center gap-1.5 mt-0.5">
                                Est. Price: ${proc.estimatedCost} · {proc.dentistName}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {proc.status === 'planned' && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => onCompleteProcedure(proc.id)}
                                className="h-7 px-2 text-[10px] font-bold text-emerald-600 hover:bg-emerald-50"
                              >
                                Done
                              </Button>
                            )}
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => onDeleteProcedure(proc.id)}
                              className="h-7 w-7 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
