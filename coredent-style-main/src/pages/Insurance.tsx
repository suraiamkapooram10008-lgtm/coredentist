// ============================================
// CoreDent PMS - Insurance Page
// Insurance management and claims tracking
// ============================================

import React, { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import {
  Plus,
  Search,
  Shield,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Send,
  AlertCircle,
  TrendingUp,
  RefreshCw,
  Loader2,
  Calendar,
  CreditCard,
} from 'lucide-react';
import { insuranceApi } from '@/services/insuranceApi';
import type { InsuranceClaim, ClaimStatus } from '@/types/insurance';

// ─────────────────────────────────────
// Helpers
// ─────────────────────────────────────

const statusConfig: Record<ClaimStatus, { label: string; className: string }> = {
  draft:     { label: 'Draft',     className: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  submitted: { label: 'Submitted', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  accepted:  { label: 'Accepted',  className: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400' },
  rejected:  { label: 'Rejected',  className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  paid:      { label: 'Paid',      className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  partial:   { label: 'Partial',   className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  appealed:  { label: 'Appealed',  className: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400' },
};

const fmt = (n?: number) =>
  n !== undefined
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
    : '—';

// ─────────────────────────────────────
// New Claim Dialog
// ─────────────────────────────────────

interface NewClaimDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onCreated: () => void;
}

function NewClaimDialog({ open, onOpenChange, onCreated }: NewClaimDialogProps) {
  const { toast } = useToast();
  const [patientId, setPatientId] = useState('');
  const [patientName, setPatientName] = useState('');
  const [insuranceId, setInsuranceId] = useState('');
  const [serviceDate, setServiceDate] = useState('');
  const [procCode, setProcCode] = useState('');
  const [procDesc, setProcDesc] = useState('');
  const [procAmount, setProcAmount] = useState('');
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const reset = () => {
    setPatientId(''); setPatientName(''); setInsuranceId('');
    setServiceDate(''); setProcCode(''); setProcDesc('');
    setProcAmount(''); setNotes('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId || !serviceDate || !procCode || !procAmount) return;
    setIsSaving(true);
    try {
      await insuranceApi.createClaim({
        patientId,
        insuranceId,
        serviceDate,
        procedures: [
          {
            procedureCode: procCode,
            description: procDesc,
            quantity: 1,
            chargedAmount: parseFloat(procAmount),
          },
        ],
        notes: notes || undefined,
      });
      toast({ title: 'Claim Created', description: `Claim submitted for ${patientName || patientId}` });
      reset();
      onOpenChange(false);
      onCreated();
    } catch {
      toast({ title: 'Error', description: 'Failed to create claim', variant: 'destructive' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>New Insurance Claim</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="nc-patient-id">Patient ID *</Label>
              <Input id="nc-patient-id" placeholder="P-001" value={patientId} onChange={e => setPatientId(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="nc-patient-name">Patient Name</Label>
              <Input id="nc-patient-name" placeholder="John Doe" value={patientName} onChange={e => setPatientName(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="nc-insurance-id">Insurance Policy ID</Label>
              <Input id="nc-insurance-id" placeholder="POL-001" value={insuranceId} onChange={e => setInsuranceId(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="nc-service-date">Service Date *</Label>
              <Input id="nc-service-date" type="date" value={serviceDate} onChange={e => setServiceDate(e.target.value)} required />
            </div>
          </div>
          <div className="border rounded-lg p-4 space-y-3 bg-muted/20">
            <p className="text-sm font-semibold text-muted-foreground">Procedure</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label htmlFor="nc-proc-code">Code *</Label>
                <Input id="nc-proc-code" placeholder="D1110" value={procCode} onChange={e => setProcCode(e.target.value)} required />
              </div>
              <div className="space-y-1">
                <Label htmlFor="nc-proc-amount">Charged ($) *</Label>
                <Input id="nc-proc-amount" type="number" min="0" step="0.01" placeholder="150.00" value={procAmount} onChange={e => setProcAmount(e.target.value)} required />
              </div>
            </div>
            <div className="space-y-1">
              <Label htmlFor="nc-proc-desc">Description</Label>
              <Input id="nc-proc-desc" placeholder="Prophylaxis – Adult" value={procDesc} onChange={e => setProcDesc(e.target.value)} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="nc-notes">Notes</Label>
            <Textarea id="nc-notes" placeholder="Additional information…" rows={2} value={notes} onChange={e => setNotes(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>Cancel</Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Saving…</> : <><Send className="h-4 w-4 mr-2" />Submit Claim</>}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────
// Claim Row
// ─────────────────────────────────────

function ClaimRow({ claim, onSubmit, isSubmitting }: { claim: InsuranceClaim; onSubmit: (id: string) => void; isSubmitting: boolean }) {
  const cfg = statusConfig[claim.status] ?? statusConfig.draft;
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-xl gap-3 hover:bg-accent/30 transition-colors">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 mt-0.5">
          <Shield className="h-5 w-5 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="font-semibold truncate">{claim.patientName}</p>
          <p className="text-xs text-muted-foreground">{claim.claimNumber} · {claim.carrierName || 'Unknown Carrier'}</p>
          <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Service: {new Date(claim.serviceDate).toLocaleDateString()}
            {claim.submittedDate && <> · Submitted: {new Date(claim.submittedDate).toLocaleDateString()}</>}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3 sm:shrink-0">
        <div className="text-right min-w-[80px]">
          <p className="text-sm font-semibold">{fmt(claim.totalAmount)}</p>
          {claim.paidAmount !== undefined && (
            <p className="text-xs text-muted-foreground">Paid: {fmt(claim.paidAmount)}</p>
          )}
        </div>
        <Badge className={`${cfg.className} border-none text-xs`}>{cfg.label}</Badge>
        {claim.status === 'draft' && (
          <Button size="sm" variant="outline" className="h-8 gap-1 text-xs" onClick={() => onSubmit(claim.id)} disabled={isSubmitting}>
            <Send className="h-3 w-3" />Submit
          </Button>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────
// Main Page
// ─────────────────────────────────────

export default function Insurance() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | 'all'>('all');
  const [activeTab, setActiveTab] = useState('claims');
  const [isNewClaimOpen, setIsNewClaimOpen] = useState(false);
  const [submittingId, setSubmittingId] = useState<string | null>(null);

  const { data: carriers = [], isLoading: isLoadingCarriers } = useQuery({
    queryKey: ['insurance', 'carriers'],
    queryFn: () => insuranceApi.getCarriers(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: claims = [], isLoading: isLoadingClaims } = useQuery({
    queryKey: ['insurance', 'claims'],
    queryFn: () => insuranceApi.getClaims(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: preAuths = [], isLoading: isLoadingPreAuths } = useQuery({
    queryKey: ['insurance', 'preAuths'],
    queryFn: () => insuranceApi.getPreAuthorizations(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: summary, isLoading: isLoadingSummary } = useQuery({
    queryKey: ['insurance', 'summary'],
    queryFn: () => insuranceApi.getSummary(),
    staleTime: 5 * 60 * 1000,
  });

  const isLoading = isLoadingCarriers || isLoadingClaims || isLoadingPreAuths || isLoadingSummary;

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['insurance'] });

  // ── Filtered claims ──
  const filteredClaims = useMemo(() => {
    return claims.filter(c => {
      const q = searchQuery.toLowerCase();
      const matchSearch = !q ||
        c.patientName.toLowerCase().includes(q) ||
        c.claimNumber.toLowerCase().includes(q) ||
        (c.carrierName || '').toLowerCase().includes(q);
      const matchStatus = statusFilter === 'all' || c.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [claims, searchQuery, statusFilter]);

  const handleSubmitClaim = async (claimId: string) => {
    setSubmittingId(claimId);
    try {
      await insuranceApi.submitClaim(claimId);
      toast({ title: 'Claim Submitted', description: 'Claim has been sent to the payer.' });
      refresh();
    } catch {
      toast({ title: 'Error', description: 'Failed to submit claim.', variant: 'destructive' });
    } finally {
      setSubmittingId(null);
    }
  };

  // Summary stat card helper
  const StatCard = ({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: React.ReactNode; color: string }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        {isLoadingSummary ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-bold">{value}</div>}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Insurance</h1>
          <p className="text-muted-foreground">Manage claims, eligibility, and EOBs</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setIsNewClaimOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Claim
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText}      label="Total Claims"    value={summary?.totalClaims ?? 0}                color="bg-blue-100 text-blue-700 dark:bg-blue-900/30" />
        <StatCard icon={Clock}         label="Pending"         value={summary?.pendingClaims ?? 0}              color="bg-amber-100 text-amber-700 dark:bg-amber-900/30" />
        <StatCard icon={CheckCircle}   label="Approved"        value={summary?.approvedClaims ?? 0}             color="bg-green-100 text-green-700 dark:bg-green-900/30" />
        <StatCard icon={DollarSign}    label="Total Paid"      value={fmt(summary?.totalPaid)}                  color="bg-violet-100 text-violet-700 dark:bg-violet-900/30" />
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="claims">Claims</TabsTrigger>
          <TabsTrigger value="eligibility">Eligibility</TabsTrigger>
          <TabsTrigger value="eobs">EOBs</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* ── Claims Tab ── */}
        <TabsContent value="claims" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search patient, claim #, carrier…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={v => setStatusFilter(v as ClaimStatus | 'all')}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="submitted">Submitted</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="appealed">Appealed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isLoadingClaims ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}
            </div>
          ) : filteredClaims.length === 0 ? (
            <Card>
              <CardContent className="py-16 text-center">
                <Shield className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                <h3 className="text-lg font-semibold mb-1">No claims found</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  {searchQuery || statusFilter !== 'all' ? 'Try adjusting your filters' : 'Submit your first claim to get started'}
                </p>
                {!searchQuery && statusFilter === 'all' && (
                  <Button onClick={() => setIsNewClaimOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />New Claim
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredClaims.map(claim => (
                <ClaimRow
                  key={claim.id}
                  claim={claim}
                  onSubmit={handleSubmitClaim}
                  isSubmitting={submittingId === claim.id}
                />
              ))}
              <p className="text-xs text-muted-foreground text-right pt-1">
                Showing {filteredClaims.length} of {claims.length} claims
              </p>
            </div>
          )}
        </TabsContent>

        {/* ── Eligibility Tab ── */}
        <TabsContent value="eligibility" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Insurance Carriers & Eligibility</h2>
          </div>
          {isLoadingCarriers ? (
            <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}</div>
          ) : carriers.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-muted-foreground">No insurance carriers configured.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {carriers.map(carrier => (
                <div key={carrier.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-accent/30 transition-colors gap-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
                      <Shield className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-semibold">{carrier.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Payer ID: {carrier.payerId || 'N/A'}
                        {carrier.phone && ` · ${carrier.phone}`}
                      </p>
                    </div>
                  </div>
                  <Badge className={carrier.isActive ? 'bg-green-100 text-green-700 border-none' : 'bg-gray-100 text-gray-600 border-none'}>
                    {carrier.isActive ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              ))}
            </div>
          )}

          {/* Pre-Authorizations */}
          {preAuths.length > 0 && (
            <div className="mt-6">
              <h3 className="text-md font-semibold mb-3">Pre-Authorizations</h3>
              <div className="space-y-3">
                {preAuths.map(auth => (
                  <div key={auth.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-accent/30 transition-colors">
                    <div>
                      <p className="font-medium">{auth.patientName || auth.patientId}</p>
                      <p className="text-xs text-muted-foreground">
                        {auth.carrierName || 'Carrier'} · Auth#: {auth.authNumber || 'Pending'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Procedures: {auth.requestedProcedures.join(', ')}
                      </p>
                    </div>
                    <Badge className={
                      auth.status === 'approved' ? 'bg-green-100 text-green-700 border-none' :
                      auth.status === 'denied' ? 'bg-red-100 text-red-700 border-none' :
                      auth.status === 'expired' ? 'bg-gray-100 text-gray-600 border-none' :
                      'bg-amber-100 text-amber-700 border-none'
                    }>
                      {auth.status.charAt(0).toUpperCase() + auth.status.slice(1)}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* ── EOBs Tab ── */}
        <TabsContent value="eobs" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Explanation of Benefits (EOBs)</h2>
          </div>

          {isLoadingClaims ? (
            <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}</div>
          ) : (
            <>
              {/* Show paid/accepted claims as EOBs */}
              {claims.filter(c => c.status === 'paid' || c.status === 'accepted' || c.status === 'partial').length === 0 ? (
                <Card>
                  <CardContent className="py-16 text-center">
                    <FileText className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
                    <h3 className="text-lg font-semibold mb-1">No EOBs yet</h3>
                    <p className="text-muted-foreground text-sm">EOB documents appear here once claims are processed by the payer.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {claims
                    .filter(c => c.status === 'paid' || c.status === 'accepted' || c.status === 'partial')
                    .map(claim => {
                      const cfg = statusConfig[claim.status];
                      return (
                        <div key={claim.id} className="p-4 border rounded-xl hover:bg-accent/30 transition-colors">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-4">
                              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30 mt-0.5">
                                <CreditCard className="h-5 w-5 text-green-600" />
                              </div>
                              <div>
                                <p className="font-semibold">{claim.patientName}</p>
                                <p className="text-xs text-muted-foreground">{claim.claimNumber} · {claim.carrierName || 'Carrier'}</p>
                                <p className="text-xs text-muted-foreground">Service: {new Date(claim.serviceDate).toLocaleDateString()}</p>
                              </div>
                            </div>
                            <div className="text-right shrink-0">
                              <Badge className={`${cfg.className} border-none text-xs mb-1`}>{cfg.label}</Badge>
                              <div className="space-y-0.5 text-sm">
                                <div className="flex justify-between gap-6 text-muted-foreground text-xs">
                                  <span>Billed:</span><span className="font-medium text-foreground">{fmt(claim.totalAmount)}</span>
                                </div>
                                {claim.approvedAmount !== undefined && (
                                  <div className="flex justify-between gap-6 text-muted-foreground text-xs">
                                    <span>Approved:</span><span className="font-medium text-foreground">{fmt(claim.approvedAmount)}</span>
                                  </div>
                                )}
                                {claim.paidAmount !== undefined && (
                                  <div className="flex justify-between gap-6 text-muted-foreground text-xs">
                                    <span>Paid:</span><span className="font-semibold text-green-600">{fmt(claim.paidAmount)}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          {claim.procedures.length > 0 && (
                            <div className="mt-3 pt-3 border-t">
                              <p className="text-xs font-semibold text-muted-foreground mb-2">Procedures</p>
                              <div className="space-y-1">
                                {claim.procedures.map((proc, i) => (
                                  <div key={i} className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">{proc.procedureCode} – {proc.description}</span>
                                    <span className="font-medium">{fmt(proc.chargedAmount)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>
              )}
            </>
          )}
        </TabsContent>

        {/* ── Reports Tab ── */}
        <TabsContent value="reports" className="space-y-4">
          <h2 className="text-lg font-semibold">Insurance Reports</h2>

          {isLoadingSummary || isLoadingClaims ? (
            <div className="grid gap-4 sm:grid-cols-2"><Skeleton className="h-40 rounded-xl" /><Skeleton className="h-40 rounded-xl" /></div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {/* Collection Rate Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-600" />
                    Collection Rate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {summary && summary.totalBilled > 0 ? (
                    <>
                      <p className="text-3xl font-bold">{Math.round((summary.totalPaid / summary.totalBilled) * 100)}%</p>
                      <p className="text-xs text-muted-foreground mt-1">{fmt(summary.totalPaid)} collected of {fmt(summary.totalBilled)} billed</p>
                    </>
                  ) : (
                    <p className="text-muted-foreground text-sm">No data</p>
                  )}
                </CardContent>
              </Card>

              {/* Denial Rate Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-red-500" />
                    Denial Rate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {summary && summary.totalClaims > 0 ? (
                    <>
                      <p className="text-3xl font-bold">{Math.round((summary.rejectedClaims / summary.totalClaims) * 100)}%</p>
                      <p className="text-xs text-muted-foreground mt-1">{summary.rejectedClaims} denied of {summary.totalClaims} total</p>
                    </>
                  ) : (
                    <p className="text-muted-foreground text-sm">No data</p>
                  )}
                </CardContent>
              </Card>

              {/* Outstanding AR Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-500" />
                    Outstanding A/R
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {summary ? (
                    <>
                      <p className="text-3xl font-bold">{fmt(summary.totalApproved - summary.totalPaid)}</p>
                      <p className="text-xs text-muted-foreground mt-1">Approved but not yet collected</p>
                    </>
                  ) : (
                    <p className="text-muted-foreground text-sm">No data</p>
                  )}
                </CardContent>
              </Card>

              {/* Claims Breakdown */}
              <Card className="sm:col-span-2 lg:col-span-3">
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Claims Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    {[
                      { label: 'Draft',     value: claims.filter(c => c.status === 'draft').length,     color: 'text-gray-600' },
                      { label: 'Submitted', value: claims.filter(c => c.status === 'submitted').length,  color: 'text-blue-600' },
                      { label: 'Paid',      value: claims.filter(c => c.status === 'paid').length,       color: 'text-green-600' },
                      { label: 'Rejected',  value: claims.filter(c => c.status === 'rejected').length,   color: 'text-red-600' },
                    ].map(item => (
                      <div key={item.label} className="p-4 rounded-lg bg-muted/40">
                        <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
                        <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* New Claim Dialog */}
      <NewClaimDialog
        open={isNewClaimOpen}
        onOpenChange={setIsNewClaimOpen}
        onCreated={refresh}
      />
    </div>
  );
}
