/**
 * Prescriptions Page
 * Comprehensive prescription management with drug search, interaction checking,
 * allergy tracking, and template-based quick prescribing.
 */

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Pill, Search, Plus, AlertTriangle, ShieldAlert, Clock, FileText,
  CheckCircle2, XCircle, ChevronRight, Zap, Users, Activity,
} from 'lucide-react';
import {
  prescriptionApi,
  FREQUENCY_OPTIONS,
  DRUG_FORMS,
  STATUS_COLORS,
  SEVERITY_COLORS,
  type Prescription,
  type PrescriptionCreateData,
  type PrescriptionTemplate,
  type InteractionCheckResponse,
  type Medication,
} from '@/services/prescriptionApi';

// ============================================
// STATUS HELPERS
// ============================================

const statusIcon = (status: string) => {
  switch (status) {
    case 'active': return <CheckCircle2 className="h-4 w-4" />;
    case 'cancelled': return <XCircle className="h-4 w-4" />;
    case 'expired': return <Clock className="h-4 w-4" />;
    default: return <FileText className="h-4 w-4" />;
  }
};

// ============================================
// WRITE PRESCRIPTION DIALOG
// ============================================

function WritePrescriptionDialog({
  open,
  onOpenChange,
  patientId,
  template,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patientId?: string;
  template?: PrescriptionTemplate | null;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [drugSearch, setDrugSearch] = useState('');
  const [selectedMed, setSelectedMed] = useState<Medication | null>(null);
  const [interactionResult, setInteractionResult] = useState<InteractionCheckResponse | null>(null);
  const [checkingInteractions, setCheckingInteractions] = useState(false);

  const [formData, setFormData] = useState<Partial<PrescriptionCreateData>>({
    patient_id: patientId || '',
    medication_name: '',
    dosage: '',
    frequency: 'bid',
    quantity: 1,
    quantity_unit: 'tablets',
    refills: 0,
    form: 'tablet',
    route: 'oral',
    substitution_allowed: true,
    dispense_as_written: false,
  });

  // Pre-fill from template
  useEffect(() => {
    if (template) {
      setFormData(prev => ({
        ...prev,
        medication_name: template.medication_name,
        generic_name: template.generic_name || undefined,
        strength: template.strength || undefined,
        form: template.form || 'tablet',
        route: template.route || 'oral',
        dosage: template.default_dosage || '',
        frequency: template.default_frequency || 'bid',
        frequency_display: template.default_frequency_display || undefined,
        duration_days: template.default_duration_days || undefined,
        quantity: template.default_quantity || 1,
        quantity_unit: template.default_quantity_unit || 'tablets',
        refills: template.default_refills || 0,
        sig: template.default_sig || undefined,
        notes_to_pharmacist: template.default_notes_to_pharmacist || undefined,
        dispense_as_written: template.dispense_as_written || false,
      }));
    }
  }, [template]);

  // Drug search
  const { data: searchResults } = useQuery({
    queryKey: ['medication-search', drugSearch],
    queryFn: () => prescriptionApi.searchMedications(drugSearch, 'all'),
    enabled: drugSearch.length >= 2,
    staleTime: 30000,
  });

  const handleSelectMedication = (med: Medication) => {
    setSelectedMed(med);
    setFormData(prev => ({
      ...prev,
      medication_name: med.name,
      medication_id: med.id,
      generic_name: med.generic_name || undefined,
      strength: med.strength || undefined,
      form: med.form || 'tablet',
      route: med.route || 'oral',
      dosage: med.default_dosage || prev.dosage,
      frequency: med.default_frequency || prev.frequency,
      duration_days: med.default_duration_days || prev.duration_days,
      quantity: med.default_quantity || prev.quantity,
    }));
    setDrugSearch('');
  };

  const handleCheckInteractions = async () => {
    if (!formData.medication_name || !formData.patient_id) return;
    setCheckingInteractions(true);
    try {
      const result = await prescriptionApi.checkInteractions(
        formData.medication_name,
        formData.patient_id
      );
      setInteractionResult(result);
    } catch {
      toast({ title: 'Error', description: 'Failed to check interactions', variant: 'destructive' });
    } finally {
      setCheckingInteractions(false);
    }
  };

  const createMutation = useMutation({
    mutationFn: (data: PrescriptionCreateData) => prescriptionApi.create(data),
    onSuccess: () => {
      toast({ title: 'Prescription Created', description: `${formData.medication_name} prescribed successfully` });
      queryClient.invalidateQueries({ queryKey: ['prescriptions'] });
      onOpenChange(false);
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to create prescription', variant: 'destructive' });
    },
  });

  const handleSubmit = () => {
    if (!formData.patient_id || !formData.medication_name || !formData.dosage || !formData.quantity) {
      toast({ title: 'Missing Fields', description: 'Please fill in all required fields', variant: 'destructive' });
      return;
    }
    const freqOption = FREQUENCY_OPTIONS.find(f => f.value === formData.frequency);
    createMutation.mutate({
      ...formData,
      frequency_display: freqOption?.label || formData.frequency,
    } as PrescriptionCreateData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Pill className="h-5 w-5 text-blue-600" />
            Write Prescription
          </DialogTitle>
          <DialogDescription>Create a new prescription with automatic safety checks</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Patient ID */}
          <div>
            <Label>Patient ID *</Label>
            <Input
              value={formData.patient_id}
              onChange={e => setFormData(prev => ({ ...prev, patient_id: e.target.value }))}
              placeholder="Enter patient ID"
            />
          </div>

          {/* Drug Search */}
          <div>
            <Label>Medication *</Label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                value={formData.medication_name || drugSearch}
                onChange={e => {
                  setDrugSearch(e.target.value);
                  setFormData(prev => ({ ...prev, medication_name: e.target.value }));
                }}
                placeholder="Search medications..."
              />
            </div>
            {searchResults?.local?.length > 0 && drugSearch.length >= 2 && (
              <div className="mt-1 border rounded-md max-h-40 overflow-y-auto bg-background shadow-lg z-50">
                {searchResults.local.map((med: Medication) => (
                  <button
                    key={med.id}
                    className="w-full text-left px-3 py-2 hover:bg-accent text-sm border-b last:border-b-0"
                    onClick={() => handleSelectMedication(med)}
                  >
                    <span className="font-medium">{med.name}</span>
                    {med.strength && <span className="text-muted-foreground ml-1">({med.strength})</span>}
                    {med.is_controlled && <Badge variant="destructive" className="ml-2 text-xs">Controlled</Badge>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Dosage Row */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <Label>Dosage *</Label>
              <Input value={formData.dosage} onChange={e => setFormData(prev => ({ ...prev, dosage: e.target.value }))} placeholder="e.g., 500mg" />
            </div>
            <div>
              <Label>Frequency *</Label>
              <Select value={formData.frequency} onValueChange={v => setFormData(prev => ({ ...prev, frequency: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {FREQUENCY_OPTIONS.map(f => (
                    <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Duration (days)</Label>
              <Input type="number" value={formData.duration_days || ''} onChange={e => setFormData(prev => ({ ...prev, duration_days: parseInt(e.target.value) || undefined }))} />
            </div>
          </div>

          {/* Quantity & Refills */}
          <div className="grid grid-cols-4 gap-3">
            <div>
              <Label>Quantity *</Label>
              <Input type="number" min={1} value={formData.quantity} onChange={e => setFormData(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))} />
            </div>
            <div>
              <Label>Unit</Label>
              <Input value={formData.quantity_unit} onChange={e => setFormData(prev => ({ ...prev, quantity_unit: e.target.value }))} />
            </div>
            <div>
              <Label>Refills</Label>
              <Input type="number" min={0} max={12} value={formData.refills} onChange={e => setFormData(prev => ({ ...prev, refills: parseInt(e.target.value) || 0 }))} />
            </div>
            <div>
              <Label>Form</Label>
              <Select value={formData.form} onValueChange={v => setFormData(prev => ({ ...prev, form: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {DRUG_FORMS.map(f => (
                    <SelectItem key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Sig & Notes */}
          <div>
            <Label>Directions (Sig)</Label>
            <Textarea value={formData.sig || ''} onChange={e => setFormData(prev => ({ ...prev, sig: e.target.value }))} placeholder="Take 1 tablet by mouth twice daily" rows={2} />
          </div>

          {/* Pharmacy */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Pharmacy</Label>
              <Input value={formData.pharmacy_name || ''} onChange={e => setFormData(prev => ({ ...prev, pharmacy_name: e.target.value }))} placeholder="Pharmacy name" />
            </div>
            <div>
              <Label>Pharmacy Phone</Label>
              <Input value={formData.pharmacy_phone || ''} onChange={e => setFormData(prev => ({ ...prev, pharmacy_phone: e.target.value }))} placeholder="Phone number" />
            </div>
          </div>

          {/* DAW */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch checked={formData.dispense_as_written} onCheckedChange={v => setFormData(prev => ({ ...prev, dispense_as_written: v, substitution_allowed: !v }))} />
              <Label>Dispense As Written (DAW)</Label>
            </div>
          </div>

          {/* Interaction Check */}
          <Button variant="outline" onClick={handleCheckInteractions} disabled={!formData.medication_name || !formData.patient_id || checkingInteractions} className="w-full">
            <ShieldAlert className="h-4 w-4 mr-2" />
            {checkingInteractions ? 'Checking...' : 'Check Drug Interactions & Allergies'}
          </Button>

          {interactionResult && (
            <div className="space-y-2">
              {interactionResult.has_interactions && interactionResult.interactions.map((ix, i) => (
                <Alert key={i} variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>⚠️ {ix.severity.toUpperCase()} Interaction: {ix.drug_a} ↔ {ix.drug_b}</AlertTitle>
                  <AlertDescription>{ix.description}</AlertDescription>
                </Alert>
              ))}
              {interactionResult.has_allergy_conflicts && interactionResult.allergy_warnings.map((aw, i) => (
                <Alert key={i} variant="destructive">
                  <ShieldAlert className="h-4 w-4" />
                  <AlertTitle>🚨 Allergy Alert</AlertTitle>
                  <AlertDescription>{aw.message}</AlertDescription>
                </Alert>
              ))}
              {!interactionResult.has_interactions && !interactionResult.has_allergy_conflicts && (
                <Alert>
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertTitle>No interactions or allergy conflicts detected</AlertTitle>
                </Alert>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={createMutation.isPending}>
            {createMutation.isPending ? 'Creating...' : 'Create Prescription'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================
// MAIN PAGE
// ============================================

export default function Prescriptions() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('prescriptions');
  const [rxDialogOpen, setRxDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<PrescriptionTemplate | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const patientIdFromUrl = searchParams.get('patient_id') || undefined;

  // Fetch prescriptions
  const { data: rxData, isLoading: rxLoading } = useQuery({
    queryKey: ['prescriptions', statusFilter, searchQuery],
    queryFn: () => prescriptionApi.list({
      status: statusFilter || undefined,
      patient_id: patientIdFromUrl,
    }),
  });

  // Fetch templates
  const { data: templateData } = useQuery({
    queryKey: ['prescription-templates'],
    queryFn: () => prescriptionApi.getTemplates(),
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => prescriptionApi.cancel(id, reason),
    onSuccess: () => {
      toast({ title: 'Prescription Cancelled' });
      queryClient.invalidateQueries({ queryKey: ['prescriptions'] });
    },
  });

  const handleQuickPrescribe = (template: PrescriptionTemplate) => {
    setSelectedTemplate(template);
    setRxDialogOpen(true);
  };

  const prescriptions: Prescription[] = rxData?.prescriptions || [];
  const templates: PrescriptionTemplate[] = templateData?.templates || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
              <Pill className="h-6 w-6" />
            </div>
            Prescription Management
          </h1>
          <p className="text-muted-foreground mt-1">Write prescriptions, manage medications, and track patient allergies</p>
        </div>
        <Button onClick={() => { setSelectedTemplate(null); setRxDialogOpen(true); }} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
          <Plus className="h-4 w-4 mr-2" /> Write Prescription
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Prescriptions</p>
                <p className="text-2xl font-bold">{prescriptions.filter(p => p.status === 'active').length}</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500 opacity-60" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Controlled Substances</p>
                <p className="text-2xl font-bold">{prescriptions.filter(p => p.is_controlled && p.status === 'active').length}</p>
              </div>
              <ShieldAlert className="h-8 w-8 text-amber-500 opacity-60" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">This Month</p>
                <p className="text-2xl font-bold">{prescriptions.length}</p>
              </div>
              <FileText className="h-8 w-8 text-green-500 opacity-60" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Templates</p>
                <p className="text-2xl font-bold">{templates.length}</p>
              </div>
              <Zap className="h-8 w-8 text-purple-500 opacity-60" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="prescriptions">Prescriptions</TabsTrigger>
          <TabsTrigger value="templates">Quick Templates</TabsTrigger>
          <TabsTrigger value="controlled">Controlled Substances</TabsTrigger>
        </TabsList>

        {/* Prescriptions Tab */}
        <TabsContent value="prescriptions" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search by medication, patient, Rx#..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40"><SelectValue placeholder="All Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Prescription List */}
          {rxLoading ? (
            <div className="text-center py-12 text-muted-foreground">Loading prescriptions...</div>
          ) : prescriptions.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Pill className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
                <h3 className="text-lg font-medium">No prescriptions found</h3>
                <p className="text-muted-foreground mt-1">Click "Write Prescription" to create one</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {prescriptions.map(rx => (
                <Card key={rx.id} className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          {statusIcon(rx.status)}
                          <Badge className={STATUS_COLORS[rx.status] || ''} variant="outline">{rx.status}</Badge>
                        </div>
                        <div>
                          <p className="font-semibold">{rx.medication_name} {rx.strength && `(${rx.strength})`}</p>
                          <p className="text-sm text-muted-foreground">
                            {rx.dosage} — {rx.frequency_display || rx.frequency} × {rx.duration_days || '∞'} days
                            {rx.quantity && ` • Qty: ${rx.quantity} ${rx.quantity_unit || ''}`}
                            {rx.refills > 0 && ` • Refills: ${rx.refills_remaining}/${rx.refills}`}
                          </p>
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <p className="font-mono text-muted-foreground">{rx.rx_number}</p>
                        <p className="text-muted-foreground">{new Date(rx.prescribed_date).toLocaleDateString()}</p>
                        {rx.is_controlled && <Badge variant="destructive" className="text-xs mt-1">Controlled</Badge>}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map(tmpl => (
              <Card key={tmpl.id} className="hover:shadow-md transition-all hover:border-blue-300 cursor-pointer" onClick={() => handleQuickPrescribe(tmpl)}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{tmpl.name}</CardTitle>
                    <Zap className="h-4 w-4 text-amber-500" />
                  </div>
                  <CardDescription>{tmpl.medication_name} {tmpl.strength}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <p>{tmpl.default_dosage} — {tmpl.default_frequency_display || tmpl.default_frequency}</p>
                    <p>Qty: {tmpl.default_quantity} {tmpl.default_quantity_unit} • {tmpl.default_duration_days} days</p>
                    {tmpl.category && <Badge variant="secondary" className="text-xs">{tmpl.category}</Badge>}
                  </div>
                  <Button size="sm" className="w-full mt-3" variant="outline">
                    <Pill className="h-3 w-3 mr-1" /> Quick Prescribe
                  </Button>
                </CardContent>
              </Card>
            ))}
            {templates.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="py-8 text-center">
                  <Zap className="h-10 w-10 mx-auto text-muted-foreground/30 mb-3" />
                  <p className="text-muted-foreground">No templates yet. Create templates for frequently prescribed medications.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Controlled Substances Tab */}
        <TabsContent value="controlled" className="space-y-4">
          <Alert>
            <ShieldAlert className="h-4 w-4" />
            <AlertTitle>DEA Compliance Tracking</AlertTitle>
            <AlertDescription>All controlled substance prescriptions are tracked with full audit trail per DEA requirements.</AlertDescription>
          </Alert>
          <div className="space-y-2">
            {prescriptions.filter(rx => rx.is_controlled).map(rx => (
              <Card key={rx.id} className="border-l-4 border-l-red-400">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{rx.medication_name} {rx.strength}</p>
                      <p className="text-sm text-muted-foreground">
                        Schedule: {rx.dea_schedule?.replace('schedule_', '').toUpperCase()} •
                        {rx.dosage} — {rx.frequency_display} • Qty: {rx.quantity}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge className={STATUS_COLORS[rx.status]} variant="outline">{rx.status}</Badge>
                      <p className="text-xs text-muted-foreground mt-1">{rx.rx_number}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {prescriptions.filter(rx => rx.is_controlled).length === 0 && (
              <Card><CardContent className="py-8 text-center text-muted-foreground">No controlled substance prescriptions</CardContent></Card>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Write Prescription Dialog */}
      <WritePrescriptionDialog
        open={rxDialogOpen}
        onOpenChange={setRxDialogOpen}
        patientId={patientIdFromUrl}
        template={selectedTemplate}
      />
    </div>
  );
}
