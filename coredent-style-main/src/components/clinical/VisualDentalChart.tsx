import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { clinicalApi, ToothCondition } from '@/services/clinicalApi';
import { format } from 'date-fns';
import { Activity, CircleDashed, Plus, ShieldAlert, CheckCircle2, History } from 'lucide-react';

interface Props {
  patientId: string;
}

const TOOTH_NUMBERS = {
  upper: Array.from({ length: 16 }, (_, i) => String(i + 1)), // 1-16
  lower: Array.from({ length: 16 }, (_, i) => String(32 - i)), // 32-17
};

const CONDITION_COLORS: Record<string, string> = {
  caries: '#ef4444', // Red
  fracture: '#f97316', // Orange
  missing: '#94a3b8', // Slate
  impacted: '#eab308', // Yellow
  wear: '#8b5cf6', // Violet
  existing_restoration: '#3b82f6', // Blue
  defective_restoration: '#ef4444', // Red (needs attention)
  abscess: '#dc2626', // Deep Red
};

export function VisualDentalChart({ patientId }: Props) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [selectedTooth, setSelectedTooth] = useState<string | null>(null);
  const [addConditionOpen, setAddConditionOpen] = useState(false);
  const [formData, setFormData] = useState({ condition_type: 'caries', surface: '', status: 'existing', severity: '', notes: '' });

  // Fetch Chart Data
  const { data: chartData, isLoading } = useQuery({
    queryKey: ['dental-chart', patientId],
    queryFn: () => clinicalApi.getPatientChart(patientId),
  });

  const { data: historyData } = useQuery({
    queryKey: ['dental-chart-history', patientId],
    queryFn: () => clinicalApi.getChartHistory(patientId),
  });

  const addMut = useMutation({
    mutationFn: (data: Partial<ToothCondition>) => clinicalApi.addCondition(patientId, data),
    onSuccess: () => {
      toast({ title: 'Condition added successfully' });
      setAddConditionOpen(false);
      queryClient.invalidateQueries({ queryKey: ['dental-chart', patientId] });
      queryClient.invalidateQueries({ queryKey: ['dental-chart-history', patientId] });
      setFormData({ condition_type: 'caries', surface: '', status: 'existing', severity: '', notes: '' });
    }
  });

  const removeMut = useMutation({
    mutationFn: (id: string) => clinicalApi.removeCondition(patientId, id),
    onSuccess: () => {
      toast({ title: 'Condition removed' });
      queryClient.invalidateQueries({ queryKey: ['dental-chart', patientId] });
    }
  });

  const conditions = chartData?.conditions || [];
  const history = historyData?.history || [];

  const getConditionsForTooth = (t: string) => conditions.filter(c => c.tooth_number === t);

  // SVG representation of a single tooth
  const renderToothSVG = (toothNum: string, isUpper: boolean) => {
    const toothConditions = getConditionsForTooth(toothNum);
    const isSelected = selectedTooth === toothNum;
    
    // Check for missing
    const isMissing = toothConditions.some(c => c.condition_type === 'missing');
    
    // Generate fill colors based on conditions (simplified representation)
    const baseColor = isMissing ? '#f1f5f9' : '#ffffff';
    let overlayColor = 'transparent';
    let hasStroke = false;
    let strokeColor = '#cbd5e1';

    if (!isMissing && toothConditions.length > 0) {
      // Find highest priority condition to show
      const priority = toothConditions[0];
      overlayColor = CONDITION_COLORS[priority.condition_type] || 'transparent';
      hasStroke = true;
      strokeColor = overlayColor;
    }

    return (
      <div 
        key={toothNum} 
        className={`flex flex-col items-center cursor-pointer transition-all ${isSelected ? 'scale-110 z-10' : 'hover:scale-105'}`}
        onClick={() => setSelectedTooth(toothNum)}
      >
        <div className={`text-xs font-semibold mb-1 ${isSelected ? 'text-blue-600' : 'text-slate-500'}`}>{toothNum}</div>
        <svg width="40" height="50" viewBox="0 0 40 50" className={`filter drop-shadow-sm ${isSelected ? 'ring-2 ring-blue-500 rounded-sm' : ''}`}>
          {/* Simple tooth shape representation */}
          <path 
            d={isUpper ? "M10 40 Q20 50 30 40 L35 10 Q20 0 5 10 Z" : "M10 10 Q20 0 30 10 L35 40 Q20 50 5 40 Z"}
            fill={baseColor}
            stroke={hasStroke ? strokeColor : "#cbd5e1"}
            strokeWidth={isSelected ? "2" : "1"}
          />
          
          {/* Condition Overlays */}
          {!isMissing && toothConditions.map((c, i) => {
            const color = CONDITION_COLORS[c.condition_type] || '#000';
            // Render surface indicators
            if (c.surface?.includes('O')) return <circle key={i} cx="20" cy="25" r="5" fill={color} opacity="0.8"/>;
            if (c.surface?.includes('M')) return <rect key={i} x="5" y="20" width="8" height="10" fill={color} opacity="0.8"/>;
            if (c.surface?.includes('D')) return <rect key={i} x="27" y="20" width="8" height="10" fill={color} opacity="0.8"/>;
            // Default center blob
            return <circle key={i} cx="20" cy="25" r="8" fill={color} opacity="0.5"/>;
          })}

          {isMissing && (
            <line x1="5" y1="5" x2="35" y2="45" stroke="#94a3b8" strokeWidth="2" />
          )}
        </svg>
      </div>
    );
  };

  const handleAddSubmit = () => {
    if (!selectedTooth) return;
    addMut.mutate({
      tooth_number: selectedTooth,
      ...formData
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-6">
        
        {/* Left Side: The Chart */}
        <div className="flex-1 space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <CircleDashed className="h-5 w-5 text-blue-500" />
                Odontogram
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Upper Arch */}
              <div className="mb-6">
                <div className="text-center text-xs text-muted-foreground mb-2 tracking-widest font-medium uppercase">Maxillary (Upper)</div>
                <div className="flex justify-center gap-1 md:gap-2">
                  {TOOTH_NUMBERS.upper.map(t => renderToothSVG(t, true))}
                </div>
              </div>

              {/* Lower Arch */}
              <div>
                <div className="flex justify-center gap-1 md:gap-2">
                  {TOOTH_NUMBERS.lower.map(t => renderToothSVG(t, false))}
                </div>
                <div className="text-center text-xs text-muted-foreground mt-2 tracking-widest font-medium uppercase">Mandibular (Lower)</div>
              </div>

              {/* Legend */}
              <div className="mt-8 flex flex-wrap gap-4 justify-center text-sm">
                {Object.entries(CONDITION_COLORS).map(([condition, color]) => (
                  <div key={condition} className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></div>
                    <span className="capitalize">{condition.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Selected Tooth Details & History */}
        <div className="w-[350px] space-y-4">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Tooth Details</CardTitle>
              <CardDescription>
                {selectedTooth ? `Tooth #${selectedTooth}` : 'Select a tooth on the chart to view details or add conditions.'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedTooth ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-lg">Tooth {selectedTooth}</h3>
                    <Button size="sm" onClick={() => setAddConditionOpen(true)}>
                      <Plus className="h-4 w-4 mr-1" /> Add
                    </Button>
                  </div>

                  <div className="space-y-3 mt-4">
                    {getConditionsForTooth(selectedTooth).length === 0 && (
                      <div className="text-center py-6 text-muted-foreground border rounded-lg bg-slate-50">
                        No conditions recorded.
                      </div>
                    )}
                    
                    {getConditionsForTooth(selectedTooth).map(c => (
                      <div key={c.id} className="p-3 border rounded-lg bg-white shadow-sm flex flex-col gap-2 relative group">
                        <div className="flex justify-between items-start">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CONDITION_COLORS[c.condition_type] || '#000' }}></div>
                            <span className="font-semibold capitalize">{c.condition_type.replace('_', ' ')}</span>
                          </div>
                          <Badge variant="outline" className="capitalize text-xs">{c.status}</Badge>
                        </div>
                        
                        <div className="text-sm text-slate-600 grid grid-cols-2 gap-1">
                          {c.surface && <span><span className="text-slate-400">Surface:</span> {c.surface}</span>}
                          {c.severity && <span><span className="text-slate-400">Severity:</span> {c.severity}</span>}
                          {c.material && <span className="col-span-2"><span className="text-slate-400">Material:</span> {c.material}</span>}
                        </div>
                        
                        {c.notes && <p className="text-xs text-slate-500 italic">"{c.notes}"</p>}
                        
                        <Button 
                          variant="destructive" 
                          size="sm" 
                          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                          onClick={() => removeMut.mutate(c.id)}
                        >
                          X
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center text-muted-foreground flex-col">
                  <Activity className="h-8 w-8 mb-2 opacity-20" />
                  Select a tooth to begin
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* History Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="h-5 w-5 text-slate-500" />
            Charting History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground">No charting history available.</div>
          ) : (
            <div className="space-y-4">
              {history.map(entry => (
                <div key={entry.id} className="flex gap-4 items-start pb-4 border-b last:border-0">
                  <div className="mt-1">
                    {entry.entry_type === 'condition' ? <ShieldAlert className="h-5 w-5 text-blue-500"/> : <CheckCircle2 className="h-5 w-5 text-green-500"/>}
                  </div>
                  <div>
                    <p className="font-medium">
                      Tooth #{entry.tooth_number} - <span className="capitalize">{entry.data?.condition_type?.replace('_', ' ')}</span> {entry.data?.action}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {format(new Date(entry.created_at), 'MMM d, yyyy h:mm a')}
                      {entry.data?.surface && ` • Surface: ${entry.data.surface}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Condition Dialog */}
      <Dialog open={addConditionOpen} onOpenChange={setAddConditionOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Condition for Tooth #{selectedTooth}</DialogTitle>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Condition</Label>
                <Select value={formData.condition_type} onValueChange={(v) => setFormData({...formData, condition_type: v})}>
                  <SelectTrigger><SelectValue/></SelectTrigger>
                  <SelectContent>
                    {Object.keys(CONDITION_COLORS).map(c => (
                      <SelectItem key={c} value={c} className="capitalize">{c.replace('_', ' ')}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Status</Label>
                <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                  <SelectTrigger><SelectValue/></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="existing">Existing</SelectItem>
                    <SelectItem value="planned">Planned Treatment</SelectItem>
                    <SelectItem value="completed">Completed Treatment</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Surface(s) (e.g. MOD)</Label>
                <Input value={formData.surface} onChange={(e) => setFormData({...formData, surface: e.target.value.toUpperCase()})} placeholder="O, M, D, B, L" />
              </div>
              <div>
                <Label>Severity</Label>
                <Input value={formData.severity} onChange={(e) => setFormData({...formData, severity: e.target.value})} placeholder="e.g. Moderate" />
              </div>
            </div>

            <div>
              <Label>Notes</Label>
              <Input value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} placeholder="Additional details..." />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setAddConditionOpen(false)}>Cancel</Button>
            <Button onClick={handleAddSubmit} disabled={addMut.isPending}>Save Condition</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}
