import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { TreatmentPlan, TreatmentStatus } from '@/types/treatmentPlan';
import { Loader2, Save, X, Sparkles } from 'lucide-react';

interface TreatmentPlanVisualBuilderProps {
  plan: TreatmentPlan;
  onUpdate: (data: {
    title: string;
    description?: string;
    patientId: string;
    patientName: string;
    status: TreatmentStatus;
    notes?: string;
  }) => Promise<void>;
  onCancel: () => void;
}

export function TreatmentPlanVisualBuilder({ plan, onUpdate, onCancel }: TreatmentPlanVisualBuilderProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [title, setTitle] = useState(plan.title || '');
  const [description, setDescription] = useState(plan.description || '');
  const [status, setStatus] = useState<TreatmentStatus>(plan.status || 'proposed');
  const [notes, setNotes] = useState(plan.notes || '');

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdate({
        title,
        description: description.trim() || undefined,
        patientId: plan.patientId,
        patientName: plan.patientName,
        status,
        notes: notes.trim() || undefined,
      });
      onCancel();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col justify-between h-[75vh] py-2 space-y-6">
      <div className="space-y-6 overflow-y-auto pr-2 custom-scrollbar flex-1">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="builder-title" className="text-xs font-black uppercase tracking-widest text-slate-400">
              Plan Title
            </Label>
            <Input
              id="builder-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="h-12 rounded-xl border-slate-200 font-bold"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="builder-status" className="text-xs font-black uppercase tracking-widest text-slate-400">
              Treatment Status
            </Label>
            <Select value={status} onValueChange={(val: any) => setStatus(val)}>
              <SelectTrigger id="builder-status" className="h-12 rounded-xl border-slate-200 font-bold">
                <SelectValue placeholder="Select status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="proposed">Proposed (Draft)</SelectItem>
                <SelectItem value="accepted">Accepted (Approved)</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="builder-desc" className="text-xs font-black uppercase tracking-widest text-slate-400">
            Description
          </Label>
          <Input
            id="builder-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Complete upper arch implant restoration and cleaning"
            className="h-12 rounded-xl border-slate-200 font-medium"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="builder-notes" className="text-xs font-black uppercase tracking-widest text-slate-400">
            Clinical Notes
          </Label>
          <Textarea
            id="builder-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Formulate medical history, billing considerations, or post-operative instructions..."
            className="min-h-[180px] rounded-xl border-slate-200 font-medium p-4"
          />
        </div>

        {/* AI Helper banner */}
        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-indigo-100/50 rounded-2xl flex items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-black text-indigo-600 uppercase tracking-widest block">AI Smart Helper</span>
            <p className="text-xs text-indigo-900 font-semibold">Generate automated insurance claims or pre-auth paperwork for this plan.</p>
          </div>
          <Button size="sm" variant="outline" className="h-8 rounded-lg border-indigo-200 text-indigo-700 bg-white font-bold flex items-center gap-1 text-xs">
            <Sparkles className="w-3.5 h-3.5 fill-amber-400 text-amber-500" /> Auto Claims
          </Button>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 shrink-0">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          className="rounded-xl font-bold h-12 border-slate-200 px-6 flex items-center gap-1"
        >
          <X className="w-4 h-4" /> Close
        </Button>
        <Button
          onClick={handleSave}
          disabled={isSaving || !title}
          className="rounded-xl font-black bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-100 h-12 px-8 flex items-center justify-center gap-2"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" /> Saving...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" /> Save Treatment Plan
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
