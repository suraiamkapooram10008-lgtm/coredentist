/**
 * Payroll Page
 * Employee compensation, commission calculation, time tracking, and payroll processing.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { format, subDays, startOfWeek, endOfWeek, subMonths, startOfMonth, endOfMonth } from 'date-fns';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Banknote, Clock, Calculator, CalendarClock, PlayCircle, Users, Activity,
  CheckCircle2, AlertTriangle, FileText, BarChart3, Clock8, Play
} from 'lucide-react';
import { payrollApi, type TimesheetEntry, type PayrollPeriod, type ProductionSummary } from '@/services/payrollApi';
import { useAuth } from '@/contexts/auth-context';

// ============================================
// HELPERS
// ============================================

const formatCurrency = (val: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

const tsStatusBadge = (status: string) => {
  switch (status) {
    case 'approved': return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Approved</Badge>;
    case 'rejected': return <Badge variant="destructive">Rejected</Badge>;
    default: return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Pending</Badge>;
  }
};

const periodStatusBadge = (status: string) => {
  switch (status) {
    case 'closed': return <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100">Closed</Badge>;
    case 'processing': return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">Processing</Badge>;
    default: return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">Open</Badge>;
  }
};

// ============================================
// TIMESHEET TAB
// ============================================

function TimeTrackingTab() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dateRange, setDateRange] = useState('this_week');

  const getDates = () => {
    const today = new Date();
    if (dateRange === 'this_week') return { start: format(startOfWeek(today), 'yyyy-MM-dd'), end: format(endOfWeek(today), 'yyyy-MM-dd') };
    if (dateRange === 'last_week') return { start: format(startOfWeek(subDays(today, 7)), 'yyyy-MM-dd'), end: format(endOfWeek(subDays(today, 7)), 'yyyy-MM-dd') };
    return {};
  };

  const { data: tsData, isLoading } = useQuery({
    queryKey: ['timesheets', dateRange],
    queryFn: () => payrollApi.listTimesheets(getDates()),
  });

  const clockInMut = useMutation({
    mutationFn: () => payrollApi.clockIn(),
    onSuccess: () => {
      toast({ title: 'Clocked In', description: `Time recorded at ${format(new Date(), 'h:mm a')}` });
      queryClient.invalidateQueries({ queryKey: ['timesheets'] });
    },
    onError: (err: any) => toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to clock in', variant: 'destructive' })
  });

  const clockOutMut = useMutation({
    mutationFn: () => payrollApi.clockOut(0),
    onSuccess: () => {
      toast({ title: 'Clocked Out', description: `Time recorded at ${format(new Date(), 'h:mm a')}` });
      queryClient.invalidateQueries({ queryKey: ['timesheets'] });
    },
    onError: (err: any) => toast({ title: 'Error', description: err.response?.data?.detail || 'Failed to clock out', variant: 'destructive' })
  });

  const approveMut = useMutation({
    mutationFn: (id: string) => payrollApi.approveTimesheet(id),
    onSuccess: () => {
      toast({ title: 'Timesheet Approved' });
      queryClient.invalidateQueries({ queryKey: ['timesheets'] });
    }
  });

  const timesheets: TimesheetEntry[] = tsData?.timesheets || [];
  const activeTimesheet = timesheets.find(t => t.user_id === user?.id && !t.clock_out);

  return (
    <div className="space-y-4">
      {/* Time Clock Card */}
      <Card className="bg-gradient-to-br from-slate-50 to-slate-100">
        <CardContent className="py-6 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold flex items-center gap-2"><Clock8 className="h-5 w-5" /> Time Clock</h3>
            {activeTimesheet ? (
              <p className="text-muted-foreground mt-1">Clocked in at {format(new Date(activeTimesheet.clock_in), 'h:mm a')}</p>
            ) : (
              <p className="text-muted-foreground mt-1">You are currently clocked out.</p>
            )}
          </div>
          <div>
            {activeTimesheet ? (
              <Button size="lg" variant="destructive" onClick={() => clockOutMut.mutate()} disabled={clockOutMut.isPending}>
                Clock Out
              </Button>
            ) : (
              <Button size="lg" className="bg-green-600 hover:bg-green-700" onClick={() => clockInMut.mutate()} disabled={clockInMut.isPending}>
                <Play className="h-4 w-4 mr-2" /> Clock In
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* History */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Timesheet History</h3>
        <Select value={dateRange} onValueChange={setDateRange}>
          <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="this_week">This Week</SelectItem>
            <SelectItem value="last_week">Last Week</SelectItem>
            <SelectItem value="all">All Time</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Employee</TableHead>
              <TableHead>In/Out</TableHead>
              <TableHead>Total Hours</TableHead>
              <TableHead>Status</TableHead>
              {(user?.role === 'owner' || user?.role === 'admin') && <TableHead className="text-right">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {timesheets.map(ts => (
              <TableRow key={ts.id}>
                <TableCell className="font-medium">{format(new Date(ts.work_date), 'MMM d, yyyy')}</TableCell>
                <TableCell>Employee {ts.user_id.substring(0,8)}</TableCell>
                <TableCell>
                  {format(new Date(ts.clock_in), 'h:mm a')} - {ts.clock_out ? format(new Date(ts.clock_out), 'h:mm a') : 'Active'}
                </TableCell>
                <TableCell>{ts.total_hours ? `${ts.total_hours}h` : '-'}</TableCell>
                <TableCell>{tsStatusBadge(ts.status)}</TableCell>
                {(user?.role === 'owner' || user?.role === 'admin') && (
                  <TableCell className="text-right">
                    {ts.status === 'pending' && ts.clock_out && (
                      <Button size="sm" variant="outline" onClick={() => approveMut.mutate(ts.id)}>Approve</Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
            {timesheets.length === 0 && (
              <TableRow><TableCell colSpan={6} className="text-center py-6 text-muted-foreground">No timesheets found.</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

// ============================================
// PAYROLL RUNS TAB
// ============================================

function PayrollRunsTab() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [periodDates, setPeriodDates] = useState({ start: '', end: '' });

  const { data, isLoading } = useQuery({ queryKey: ['payroll-periods'], queryFn: () => payrollApi.listPeriods() });

  const createMut = useMutation({
    mutationFn: (d: any) => payrollApi.createPeriod(d),
    onSuccess: () => {
      toast({ title: 'Payroll Period Created' });
      setCreateOpen(false);
      queryClient.invalidateQueries({ queryKey: ['payroll-periods'] });
    }
  });

  const processMut = useMutation({
    mutationFn: (id: string) => payrollApi.processPeriod(id),
    onSuccess: () => {
      toast({ title: 'Payroll Processed successfully' });
      queryClient.invalidateQueries({ queryKey: ['payroll-periods'] });
    }
  });

  const periods: PayrollPeriod[] = data?.periods || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Payroll Runs</h3>
        <Button onClick={() => setCreateOpen(true)}><CalendarClock className="h-4 w-4 mr-2"/> Open New Period</Button>
      </div>

      <div className="grid gap-4">
        {periods.map(p => (
          <Card key={p.id} className={p.status === 'open' ? 'border-blue-200 shadow-sm' : ''}>
            <CardContent className="py-5">
              <div className="flex items-center justify-between">
                <div className="flex gap-4">
                  <div className="p-3 bg-slate-100 rounded-lg">
                    <Banknote className="h-6 w-6 text-slate-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold">{format(new Date(p.period_start), 'MMM d, yyyy')} - {format(new Date(p.period_end), 'MMM d, yyyy')}</h4>
                    <div className="flex items-center gap-3 mt-1">
                      {periodStatusBadge(p.status)}
                      {p.status === 'closed' && (
                        <span className="text-sm text-muted-foreground font-mono">Gross: {formatCurrency(p.total_gross)} • Commissions: {formatCurrency(p.total_commissions)}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div>
                  {p.status === 'open' && (
                    <Button onClick={() => processMut.mutate(p.id)} disabled={processMut.isPending}>
                      {processMut.isPending ? 'Processing...' : 'Process Payroll'}
                    </Button>
                  )}
                  {p.status === 'closed' && (
                    <Button variant="outline"><FileText className="h-4 w-4 mr-2"/> View Report</Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Open New Payroll Period</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Start Date</Label>
                <Input type="date" value={periodDates.start} onChange={e=>setPeriodDates(p=>({...p,start:e.target.value}))}/>
              </div>
              <div>
                <Label>End Date</Label>
                <Input type="date" value={periodDates.end} onChange={e=>setPeriodDates(p=>({...p,end:e.target.value}))}/>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={() => createMut.mutate({ period_start: periodDates.start, period_end: periodDates.end })} disabled={!periodDates.start || !periodDates.end}>Create Period</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ============================================
// MAIN PAGE
// ============================================

export default function Payroll() {
  const [activeTab, setActiveTab] = useState('timesheets');
  const [prodMonth, setProdMonth] = useState('this_month');

  const getProdDates = () => {
    const today = new Date();
    if (prodMonth === 'this_month') return { start: format(startOfMonth(today), 'yyyy-MM-dd'), end: format(endOfMonth(today), 'yyyy-MM-dd') };
    if (prodMonth === 'last_month') return { start: format(startOfMonth(subMonths(today, 1)), 'yyyy-MM-dd'), end: format(endOfMonth(subMonths(today, 1)), 'yyyy-MM-dd') };
    return { start: format(startOfMonth(today), 'yyyy-MM-dd'), end: format(endOfMonth(today), 'yyyy-MM-dd') };
  };

  const dates = getProdDates();
  const { data: prodData } = useQuery({
    queryKey: ['production', dates.start, dates.end],
    queryFn: () => payrollApi.getProductionSummary(dates.start, dates.end),
  });

  const summaries: ProductionSummary[] = prodData?.summaries || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
            <Calculator className="h-6 w-6" />
          </div>
          Payroll & Commissions
        </h1>
        <p className="text-muted-foreground mt-1">Manage employee compensation, time tracking, and production commissions</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="timesheets">Time Tracking</TabsTrigger>
          <TabsTrigger value="production">Production & Commissions</TabsTrigger>
          <TabsTrigger value="payroll">Payroll Runs</TabsTrigger>
          <TabsTrigger value="compensation">Compensation Setup</TabsTrigger>
        </TabsList>

        <TabsContent value="timesheets" className="mt-4">
          <TimeTrackingTab />
        </TabsContent>

        <TabsContent value="payroll" className="mt-4">
          <PayrollRunsTab />
        </TabsContent>

        <TabsContent value="production" className="mt-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Provider Production</h3>
            <Select value={prodMonth} onValueChange={setProdMonth}>
              <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="this_month">This Month</SelectItem>
                <SelectItem value="last_month">Last Month</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {summaries.map(s => (
              <Card key={s.user_id}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{s.user_name}</CardTitle>
                  <CardDescription className="capitalize">{s.role}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gross Prod.</span>
                      <span className="font-semibold">{formatCurrency(s.total_production)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Collections</span>
                      <span className="font-semibold text-green-600">{formatCurrency(s.total_collections)}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t">
                      <span className="text-sm text-muted-foreground">Procedures</span>
                      <span className="text-sm font-medium">{s.procedures_completed}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {summaries.length === 0 && (
              <div className="col-span-full p-8 text-center border rounded-lg bg-slate-50 text-muted-foreground">
                <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                No production logged for this period
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="compensation" className="mt-4">
          <Card>
            <CardContent className="py-12 text-center">
              <Users className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
              <h3 className="text-lg font-medium">Compensation & Commission Setup</h3>
              <p className="text-muted-foreground mt-1">Configure employee pay rates, salary structures, and commission rules here.</p>
              <Button className="mt-4" variant="outline">Manage Compensation</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
