import { 
  CreditCard, 
  Calendar, 
  Plus, 
  FileText, 
  Receipt, 
  Clock, 
  AlertCircle,
  MoreVertical,
  Download,
  Send,
  Zap,
  ArrowRight,
  ShieldCheck,
  Split
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

export default function BillingPortal() {

  const invoices = [
    { id: 'INV-2026-0042', patient: 'John Doe', amount: 1250.00, status: 'Overdue', date: '2026-03-15' },
    { id: 'INV-2026-0051', patient: 'Jane Smith', amount: 450.00, status: 'Paid', date: '2026-04-01' },
    { id: 'INV-2026-0055', patient: 'Robert Chen', amount: 2800.00, status: 'Pending', date: '2026-04-05' },
  ];

  const paymentPlans = [
    { 
      id: 'PLN-9901', 
      patient: 'Sarah Wilson', 
      total: 3600.00, 
      paid: 1200.00, 
      status: 'Active', 
      nextPayment: '2026-05-01',
      progress: 33
    },
  ];

  return (
    <div className="p-8 space-y-8 max-w-[1400px] mx-auto animate-in fade-in duration-700">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6 border-slate-200">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight flex items-center gap-3">
            Intelligent Billing
            <Badge variant="outline" className="bg-emerald-50 text-emerald-600 border-emerald-100 font-bold uppercase tracking-widest text-[10px] py-1">Fintech Engine</Badge>
          </h1>
          <p className="text-slate-500 font-medium mt-1">Automated collections, payment plans, and statement generation.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="h-12 px-6 rounded-2xl font-bold border-slate-200 hover:bg-slate-50">
            <FileText className="w-4 h-4 mr-2" /> Bulk Statements
          </Button>
          <Button className="h-12 px-8 rounded-2xl font-black bg-emerald-600 hover:bg-emerald-700 shadow-xl shadow-emerald-100 transition-all hover:scale-[1.02] active:scale-95 text-white">
            <Plus className="w-4 h-4 mr-2" /> New Payment Plan
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content (2/3) */}
        <div className="lg:col-span-2 space-y-8">
          <Tabs defaultValue="plans" className="w-full">
            <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-white overflow-hidden">
               <TabsList className="h-16 bg-slate-50/50 p-2 gap-2 border-b border-slate-100 w-full justify-start px-6 rounded-none">
                <TabsTrigger value="plans" className="rounded-xl px-6 font-bold text-slate-500 data-[state=active]:bg-white data-[state=active]:text-emerald-600 data-[state=active]:shadow-sm">
                  Active Payment Plans
                </TabsTrigger>
                <TabsTrigger value="invoices" className="rounded-xl px-6 font-bold text-slate-500 data-[state=active]:bg-white data-[state=active]:text-emerald-600 data-[state=active]:shadow-sm">
                  Recent Invoices
                </TabsTrigger>
                <TabsTrigger value="virtual" className="rounded-xl px-6 font-bold text-slate-500 data-[state=active]:bg-white data-[state=active]:text-emerald-600 data-[state=active]:shadow-sm">
                  Virtual Terminal
                </TabsTrigger>
              </TabsList>

              <TabsContent value="plans" className="p-8 m-0">
                <div className="space-y-6">
                   {paymentPlans.map((plan) => (
                      <div key={plan.id} className="p-8 rounded-3xl border-2 border-slate-100 hover:border-emerald-200 transition-all group">
                         <div className="flex justify-between items-start mb-6">
                            <div className="flex gap-4">
                               <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                                  <Split className="w-7 h-7" />
                               </div>
                               <div>
                                  <h3 className="text-xl font-black text-slate-900 tracking-tight">{plan.patient}</h3>
                                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Plan ID: {plan.id}</p>
                               </div>
                            </div>
                            <Badge className="bg-emerald-500 text-white border-none font-bold py-1.5 px-4 rounded-xl">{plan.status}</Badge>
                         </div>
                         
                         <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                            <div className="space-y-1">
                               <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Total Amount</p>
                               <p className="text-2xl font-black text-slate-900">${plan.total.toLocaleString()}</p>
                            </div>
                            <div className="space-y-1 text-emerald-600">
                               <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Remaining</p>
                               <p className="text-2xl font-black">${(plan.total - plan.paid).toLocaleString()}</p>
                            </div>
                            <div className="space-y-1">
                               <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Next Auto-Pay</p>
                               <p className="text-lg font-bold text-slate-700 flex items-center gap-2">
                                  <Calendar className="w-4 h-4 text-emerald-500" />
                                  {plan.nextPayment}
                               </p>
                            </div>
                         </div>

                         <div className="space-y-3">
                            <div className="flex justify-between items-end">
                               <span className="text-sm font-bold text-slate-500">Repayment Progress</span>
                               <span className="text-sm font-black text-emerald-600">{plan.progress}%</span>
                            </div>
                            <Progress value={plan.progress} className="h-2.5 bg-slate-100" />
                         </div>

                         <div className="mt-8 flex gap-3">
                            <Button className="rounded-xl font-bold bg-slate-900 hover:bg-slate-800 text-white overflow-hidden group">
                               Update Plan <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
                            </Button>
                            <Button variant="outline" className="rounded-xl font-bold border-slate-200">View Statement</Button>
                         </div>
                      </div>
                   ))}
                </div>
              </TabsContent>

              <TabsContent value="invoices" className="p-8">
                <div className="space-y-4">
                   {invoices.map((inv) => (
                      <div key={inv.id} className="flex items-center justify-between p-6 rounded-2xl border border-slate-100 hover:bg-slate-50/50 transition-colors">
                         <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500">
                               <FileText className="w-5 h-5" />
                            </div>
                            <div>
                               <p className="font-bold text-slate-900">{inv.patient}</p>
                               <p className="text-xs text-slate-400 font-medium">{inv.id} • {inv.date}</p>
                            </div>
                         </div>
                         <div className="flex items-center gap-8">
                            <p className="font-black text-slate-900">${inv.amount.toLocaleString()}</p>
                            <Badge variant="outline" className={cn(
                               "font-black uppercase tracking-widest text-[9px] px-2 py-0.5",
                               inv.status === 'Paid' ? "bg-emerald-50 text-emerald-600 border-emerald-100" :
                               inv.status === 'Overdue' ? "bg-red-50 text-red-600 border-red-100" :
                               "bg-amber-50 text-amber-600 border-amber-100"
                            )}>
                               {inv.status}
                            </Badge>
                            <DropdownMenu>
                               <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-lg"><MoreVertical className="w-4 h-4" /></Button>
                               </DropdownMenuTrigger>
                               <DropdownMenuContent align="end" className="rounded-xl border-slate-200 shadow-xl">
                                  <DropdownMenuItem className="font-bold text-slate-600 flex gap-2"><Send className="w-4 h-4" /> Resend Statement</DropdownMenuItem>
                                  <DropdownMenuItem className="font-bold text-slate-600 flex gap-2"><Download className="w-4 h-4" /> Download PDF</DropdownMenuItem>
                                  <DropdownMenuItem className="font-bold text-red-600 flex gap-2"><AlertCircle className="w-4 h-4" /> Cancel Invoice</DropdownMenuItem>
                               </DropdownMenuContent>
                            </DropdownMenu>
                         </div>
                      </div>
                   ))}
                </div>
              </TabsContent>
            </Card>
          </Tabs>

          <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-indigo-950 text-white overflow-hidden">
             <CardContent className="p-12 flex flex-col md:flex-row items-center gap-12">
                <div className="flex-1 space-y-6">
                   <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-[10px] font-black uppercase tracking-widest">
                      <Zap className="w-3 h-3" /> Auto-Collection Sequence Active
                   </div>
                   <h2 className="text-3xl font-black tracking-tight leading-tight">Your practice collected <span className="text-emerald-400">$8,420</span> automatically this month.</h2>
                   <p className="text-indigo-200 font-medium leading-relaxed">
                      Our smart reminder engine nudged 14 patients with overdue balances. 9 of them paid within 2 hours of receiving their SMS statement.
                   </p>
                   <Button className="h-12 px-8 rounded-xl bg-white text-indigo-900 font-black hover:bg-slate-100 transition-all">Configure Reminders</Button>
                </div>
                <div className="w-full md:w-[240px] aspect-square rounded-[3rem] border border-white/10 bg-white/5 backdrop-blur-3xl flex items-center justify-center relative">
                   <div className="absolute inset-4 rounded-[2.5rem] border border-white/5 bg-gradient-to-br from-emerald-500/20 to-transparent" />
                   <Receipt className="w-20 h-20 text-emerald-400" />
                </div>
             </CardContent>
          </Card>
        </div>

        {/* Right Sidebar (1/3) */}
        <div className="space-y-8">
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-white overflow-hidden">
             <CardHeader className="p-10 pb-0">
                <CardTitle className="text-xl font-black tracking-tight text-slate-800">Secure Vault</CardTitle>
                <CardDescription className="font-bold text-slate-400 uppercase text-[10px] tracking-widest">PCI-DSS Tokenized Cards</CardDescription>
             </CardHeader>
             <CardContent className="p-10 space-y-8">
                <div className="p-6 rounded-3xl bg-slate-50 border border-slate-100 space-y-6">
                   <div className="flex justify-between items-center">
                      <div className="flex gap-3 items-center">
                         <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white">
                            <CreditCard className="w-6 h-6" />
                         </div>
                         <span className="font-black text-slate-900">•••• 4242</span>
                      </div>
                      <Badge variant="secondary" className="bg-white border-slate-200 text-slate-400">Default</Badge>
                   </div>
                   <div className="space-y-1">
                      <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Cardholder</p>
                      <p className="text-sm font-bold text-slate-700">Sarah Wilson</p>
                   </div>
                </div>

                <Button variant="outline" className="w-full h-14 rounded-2xl border-2 border-slate-100 border-dashed hover:border-blue-200 hover:bg-blue-50 text-blue-600 font-bold transition-all">
                   <Plus className="w-4 h-4 mr-2" /> Add New Card
                </Button>

                <Separator className="bg-slate-100" />

                <div className="space-y-4">
                   <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                         <ShieldCheck className="w-4 h-4" />
                      </div>
                      <span className="text-sm font-bold text-slate-800">Bank-level encryption (AES-256)</span>
                   </div>
                   <div className="flex items-center gap-3 text-slate-400">
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                         <Clock className="w-4 h-4" />
                      </div>
                      <span className="text-sm font-bold">Auto-pay enabled for Sarah</span>
                   </div>
                </div>
             </CardContent>
           </Card>

           <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-emerald-600 text-white overflow-hidden">
              <CardContent className="p-10 space-y-6">
                 <h3 className="text-2xl font-black tracking-tight leading-tight">Build Custom Payment Plan</h3>
                 <p className="text-emerald-100 text-sm font-medium">Split large treatment costs into manageable monthly installments.</p>
                 <div className="space-y-4 pt-2">
                    <div className="space-y-2">
                       <Label className="text-xs font-black uppercase tracking-widest text-emerald-200">Treatment Cost</Label>
                       <Input className="bg-white/10 border-white/20 text-white h-12 rounded-xl text-lg font-black placeholder:text-white/40" placeholder="$0.00" />
                    </div>
                    <div className="space-y-2">
                       <Label className="text-xs font-black uppercase tracking-widest text-emerald-200">Months</Label>
                       <Input type="number" className="bg-white/10 border-white/20 text-white h-12 rounded-xl text-lg font-black" defaultValue={12} />
                    </div>
                    <Button className="w-full h-14 rounded-2xl bg-white text-emerald-700 font-black hover:bg-slate-100 shadow-2xl shadow-emerald-700/20">Calculate Installments</Button>
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
}
