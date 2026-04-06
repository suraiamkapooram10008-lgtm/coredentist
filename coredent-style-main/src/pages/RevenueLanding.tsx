import { 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  DollarSign, 
  BarChart3, 
  ArrowUpRight, 
  ArrowDownRight,
  Filter,
  Download,
  ShieldCheck,
  Zap,
  Info
} from 'lucide-react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

export default function RevenueLanding() {
  const stats = [
    { label: 'Net Production', value: '$242,500', trend: '+12.5%', icon: DollarSign, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Claims Pending', value: '48', trend: '-2.4%', icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Collection Rate', value: '98.2%', trend: '+0.5%', icon: TrendingUp, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Insurance A/R', value: '$84,200', trend: '+5.2%', icon: BarChart3, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  const recentClaims = [
    { id: 'CLM-10024', patient: 'John Smith', carrier: 'Delta Dental', amount: 1250.00, status: 'Submitted', date: '2026-04-05' },
    { id: 'CLM-10023', patient: 'Sarah Wilson', carrier: 'Aetna', amount: 450.00, status: 'Paid', date: '2026-04-04' },
    { id: 'CLM-10022', patient: 'Robert Chen', carrier: 'Cigna', amount: 2800.00, status: 'Denied', date: '2026-04-04' },
    { id: 'CLM-10021', patient: 'Maria Garcia', carrier: 'MetLife', amount: 125.00, status: 'Review', date: '2026-04-03' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-[1600px] mx-auto animate-in fade-in duration-700">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6 border-slate-200">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight flex items-center gap-3">
            Revenue Cycle Hub
            <Badge variant="outline" className="bg-blue-50 text-blue-600 border-blue-100 font-bold uppercase tracking-widest text-[10px] py-1">v2.0 Beta</Badge>
          </h1>
          <p className="text-slate-500 font-medium mt-1">Intelligent claims management and financial diagnostics.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="h-12 px-6 rounded-2xl font-bold border-slate-200 hover:bg-slate-50">
            <Download className="w-4 h-4 mr-2" /> Export RCM Data
          </Button>
          <Button className="h-12 px-8 rounded-2xl font-black bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all hover:scale-[1.02] active:scale-95 text-white">
            <TrendingUp className="w-4 h-4 mr-2" /> Run Revenue Audit
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => (
          <Card key={idx} className="border-none shadow-[0_15px_40px_rgba(0,0,0,0.04)] rounded-[2rem] overflow-hidden group hover:shadow-[0_20px_50px_rgba(0,0,0,0.06)] transition-all duration-500">
            <CardContent className="p-8 space-y-4">
              <div className="flex justify-between items-start">
                <div className={cn("p-4 rounded-3xl transition-transform group-hover:scale-110", stat.bg)}>
                  <stat.icon className={cn("w-6 h-6", stat.color)} />
                </div>
                <div className={cn(
                  "flex items-center gap-1 text-xs font-black px-2 py-1 rounded-full",
                  stat.trend.startsWith('+') ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"
                )}>
                  {stat.trend.startsWith('+') ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {stat.trend}
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-slate-400 font-bold text-xs uppercase tracking-[0.15em]">{stat.label}</p>
                <h3 className="text-3xl font-black text-slate-900 tracking-tighter">{stat.value}</h3>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left: Operations & Claims (2/3) */}
        <div className="lg:col-span-2 space-y-8">
          <Tabs defaultValue="claims" className="w-full">
            <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-white overflow-hidden">
              <TabsList className="h-16 bg-slate-50/50 p-2 gap-2 border-b border-slate-100 w-full justify-start px-6 rounded-none">
                <TabsTrigger value="claims" className="rounded-xl px-6 font-bold text-slate-500 data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">
                  Electronic Claims
                </TabsTrigger>
                <TabsTrigger value="aging" className="rounded-xl px-6 font-bold text-slate-500 data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">
                  Insurance Aging
                </TabsTrigger>
                <TabsTrigger value="denials" className="rounded-xl px-6 font-bold text-slate-500 data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">
                  Denial Management
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="claims" className="p-0 m-0">
                <div className="p-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-black text-slate-800 tracking-tight">Recent EDI Activities</h3>
                    <div className="flex gap-2">
                       <Button size="sm" variant="outline" className="rounded-xl font-bold border-slate-200">
                        <Filter className="w-3 h-3 mr-1" /> Filter
                       </Button>
                    </div>
                  </div>
                  
                  <div className="border rounded-2xl overflow-hidden border-slate-100">
                    <Table>
                      <TableHeader className="bg-slate-50/50">
                        <TableRow className="hover:bg-transparent border-slate-100">
                          <TableHead className="font-bold text-slate-500 uppercase text-[10px] tracking-widest pl-6">Claim ID</TableHead>
                          <TableHead className="font-bold text-slate-500 uppercase text-[10px] tracking-widest text-center">Patient</TableHead>
                          <TableHead className="font-bold text-slate-500 uppercase text-[10px] tracking-widest text-right">Fee</TableHead>
                          <TableHead className="font-bold text-slate-500 uppercase text-[10px] tracking-widest text-center">Status</TableHead>
                          <TableHead className="font-bold text-slate-500 uppercase text-[10px] tracking-widest pr-6 text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {recentClaims.map((claim) => (
                          <TableRow key={claim.id} className="hover:bg-slate-50/50 border-slate-50 transition-colors">
                            <TableCell className="pl-6">
                              <span className="font-black text-slate-900 font-mono tracking-tight">{claim.id}</span>
                              <p className="text-[10px] text-slate-400 font-bold uppercase mt-0.5">{claim.carrier}</p>
                            </TableCell>
                            <TableCell className="text-center">
                              <span className="font-bold text-slate-700">{claim.patient}</span>
                            </TableCell>
                            <TableCell className="text-right">
                              <span className="font-black text-slate-900 tracking-tighter">${claim.amount.toLocaleString()}</span>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant="outline" className={cn(
                                "font-black uppercase tracking-widest text-[9px] py-0.5 px-2 rounded-md border-2",
                                claim.status === 'Paid' ? "bg-emerald-50 text-emerald-600 border-emerald-100" :
                                claim.status === 'Denied' ? "bg-red-50 text-red-600 border-red-100" :
                                "bg-blue-50 text-blue-600 border-blue-100"
                              )}>
                                {claim.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="pr-6 text-right">
                              <Button variant="ghost" size="sm" className="rounded-lg h-8 px-3 font-bold text-blue-600 hover:text-blue-700 hover:bg-blue-50">View EOB</Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  
                  <div className="bg-slate-50 rounded-2xl p-6 flex flex-col md:flex-row items-center gap-6 border border-slate-100">
                    <div className="w-12 h-12 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-600 shrink-0">
                      <Zap className="w-6 h-6" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-black text-slate-800">Auto-verify active for 144 patients</p>
                      <p className="text-xs text-slate-500 font-medium leading-relaxed">Our AI verified coverage for 12 patients scheduled for tomorrow. 1 patient requires manual review.</p>
                    </div>
                    <Button variant="outline" className="rounded-xl font-bold border-slate-200">Manage Rules</Button>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="aging" className="p-8">
                <div className="flex items-center justify-center h-[300px] text-slate-400 font-bold border-2 border-dashed border-slate-100 rounded-3xl">
                  Aging Workflow under construction
                </div>
              </TabsContent>
              <TabsContent value="denials" className="p-8">
                <div className="flex items-center justify-center h-[300px] text-slate-400 font-bold border-2 border-dashed border-slate-100 rounded-3xl">
                  Denial Management module pending
                </div>
              </TabsContent>
            </Card>
          </Tabs>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2rem] bg-indigo-900 text-white overflow-hidden relative">
              <div className="absolute top-0 right-0 p-8 opacity-20 transform translate-x-4 -translate-y-4">
                <ShieldCheck className="w-24 h-24" />
              </div>
              <CardContent className="p-10 space-y-6">
                <div className="space-y-2">
                  <h3 className="text-2xl font-black tracking-tight">Eligibility Engine</h3>
                  <p className="text-indigo-200 text-sm font-medium leading-relaxed">Real-time verification against 800+ payers via DentalXChange (837/835).</p>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <span className="text-xs font-black uppercase tracking-widest text-indigo-300">Payer Connectivity</span>
                    <span className="text-xs font-black">99.9%</span>
                  </div>
                  <Progress value={99.9} className="h-1.5 bg-indigo-800/50" />
                </div>
                <Button className="w-full h-12 rounded-xl bg-white text-indigo-900 font-black hover:bg-slate-100 shadow-xl shadow-indigo-900">Check New Eligibility</Button>
              </CardContent>
            </Card>

            <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2rem] bg-emerald-600 text-white overflow-hidden relative">
              <div className="absolute top-0 right-0 p-8 opacity-20 transform translate-x-4 -translate-y-4">
                <DollarSign className="w-24 h-24" />
              </div>
              <CardContent className="p-10 space-y-6">
                <div className="space-y-2">
                  <h3 className="text-2xl font-black tracking-tight">Auto-Collections</h3>
                  <p className="text-emerald-100 text-sm font-medium leading-relaxed">Smart SMS/Email follow-ups for outstanding patient balances.</p>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <span className="text-xs font-black uppercase tracking-widest text-emerald-200">Active Sequences</span>
                    <span className="text-xs font-black">12 Active</span>
                  </div>
                  <Progress value={75} className="h-1.5 bg-emerald-700/50" />
                </div>
                <Button className="w-full h-12 rounded-xl bg-white text-emerald-700 font-black hover:bg-slate-100 shadow-xl shadow-emerald-700">Review Campaigns</Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right: Diagnostics & Trends (1/3) */}
        <div className="space-y-8">
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-white overflow-hidden">
             <CardHeader className="p-10 pb-0">
                <CardTitle className="text-xl font-black tracking-tight text-slate-800">Payer Analytics</CardTitle>
                <CardDescription className="font-bold text-slate-400 uppercase text-[10px] tracking-widest">Collection time by Carrier</CardDescription>
             </CardHeader>
             <CardContent className="p-10 space-y-8">
                {[
                  { name: 'Delta Dental', time: '12 Days', pct: 90, color: 'bg-blue-600' },
                  { name: 'Aetna', time: '14 Days', pct: 82, color: 'bg-blue-400' },
                  { name: 'Cigna', time: '19 Days', pct: 65, color: 'bg-amber-500' },
                  { name: 'MetLife', time: '22 Days', pct: 45, color: 'bg-red-500' },
                ].map((payer, idx) => (
                  <div key={idx} className="space-y-3 group cursor-pointer">
                    <div className="flex justify-between items-center">
                      <span className="font-black text-slate-700 text-sm">{payer.name}</span>
                      <span className="font-black text-slate-400 text-[10px] uppercase tracking-wider">{payer.time} avg</span>
                    </div>
                    <Progress value={payer.pct} className="h-2 bg-slate-50 transition-all duration-300 group-hover:h-3" />
                  </div>
                ))}
                
                <Separator className="bg-slate-100" />
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600">
                      <AlertCircle className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-bold text-slate-800">Critical: 8 denials requiring appeal today</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-bold text-slate-800">Optimal: Payer payment pace increased 22%</span>
                  </div>
                </div>
             </CardContent>
           </Card>

           <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-gradient-to-br from-blue-600 to-indigo-700 text-white overflow-hidden">
              <CardContent className="p-10 space-y-6 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-white/20 backdrop-blur-md mb-2">
                  <Info className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-black tracking-tight">RCM Intelligence</h3>
                <p className="text-blue-100 text-sm font-medium leading-relaxed">
                  Our system analyzed your clinical patterns and identified $12,400 in unbilled preventive procedures from last week.
                </p>
                <Button className="w-full h-14 rounded-2xl bg-white text-blue-600 font-black hover:bg-slate-100 shadow-2xl shadow-blue-900/40">Generate Recovery List</Button>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
}

interface SeparatorProps { className?: string }
function Separator({ className }: SeparatorProps) {
  return <div className={cn("h-px w-full", className)} />;
}
