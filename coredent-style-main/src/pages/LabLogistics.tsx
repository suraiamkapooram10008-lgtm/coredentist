import { useState } from 'react';
import { 
  Package, 
  Truck, 
  Clock, 
  ArrowRight, 
  Search, 
  Plus, 
  FileText, 
  User, 
  ExternalLink,
  Microscope,
  DollarSign,
  Boxes
} from 'lucide-react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export default function LabLogistics() {
  const [selectedCase, setSelectedCase] = useState<string | null>('LAB-5521');

  const activeCases = [
    { 
      id: 'LAB-5521', 
      patient: 'Olivia Chen', 
      provider: 'Dr. Sarah Smith',
      type: 'Zirconia Crown (#14)', 
      status: 'Shipped', 
      dueDate: '2026-04-12',
      lab: 'Pioneer Dental Lab',
      tracking: '1Z999AA10123456784',
      carrier: 'UPS',
      eta: 'Apr 10, 10:30 AM',
      progress: 65,
      urgency: 'medium'
    },
    { 
      id: 'LAB-5518', 
      patient: 'Robert Brown', 
      provider: 'Dr. Michael Chen',
      type: 'Full Arch Denture (Max)', 
      status: 'Quality Check', 
      dueDate: '2026-04-18',
      lab: 'Global Aesthetics',
      progress: 45,
      urgency: 'low'
    },
    { 
      id: 'LAB-5582', 
      patient: 'Emily Davis', 
      provider: 'Dr. Sarah Smith',
      type: 'Immediate Partial (#7, #10)', 
      status: 'On Hold', 
      dueDate: '2026-04-10',
      lab: 'Pioneer Dental Lab',
      progress: 20,
      urgency: 'high',
      issue: 'Shade mismatch in photos'
    },
  ];

  const milestones = [
    { title: 'Case Prescribed', date: 'Apr 01', completed: true },
    { title: 'Impression Scanned (iTero)', date: 'Apr 02', completed: true },
    { title: 'Sent to Lab', date: 'Apr 02', completed: true },
    { title: 'Lab Fabrication', date: 'Apr 04', completed: true },
    { title: 'Quality Control', date: 'Apr 07', completed: true },
    { title: 'Shipped (UPS)', date: 'Apr 08', completed: true, current: true },
    { title: 'Delivered @ Office', date: 'Apr 10 (Est)', completed: false },
    { title: 'Patient Seating', date: 'Apr 12 (Scheduled)', completed: false },
  ];

  return (
    <div className="p-10 space-y-10 max-w-[1700px] mx-auto animate-in fade-in duration-1000">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b pb-8 border-slate-100">
        <div className="space-y-1">
          <h1 className="text-4xl font-black text-slate-900 tracking-tight flex items-center gap-3">
             <Microscope className="w-8 h-8 text-indigo-600" />
             Lab Logistics Hub
          </h1>
          <p className="text-slate-500 font-medium">Track high-fidelity prosthetic cases from impression to delivery.</p>
        </div>
        <div className="flex gap-3">
           <Button variant="outline" className="h-12 px-6 rounded-2xl font-bold border-slate-200 hover:bg-slate-50">
            <Boxes className="w-4 h-4 mr-2" /> Lab Inventory
          </Button>
          <Button className="h-12 px-8 rounded-2xl font-black bg-indigo-600 hover:bg-indigo-700 shadow-xl shadow-indigo-100 transition-all hover:scale-[1.02] active:scale-95 text-white">
            <Plus className="w-4 h-4 mr-2" /> New Lab Order
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* Left: Case List (1/3) */}
        <div className="xl:col-span-1 space-y-6">
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden">
              <CardHeader className="p-8 pb-4">
                 <div className="flex justify-between items-center">
                    <CardTitle className="text-xl font-black tracking-tight">Active Cases</CardTitle>
                    <Badge variant="outline" className="bg-slate-50 text-slate-500 border-slate-100 font-bold">{activeCases.length} Orders</Badge>
                 </div>
                 <div className="relative mt-4">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input className="w-full bg-slate-50 border-none rounded-xl h-12 pl-12 pr-6 text-sm font-bold placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-600/20 outline-none" placeholder="Search by patient or ID..." />
                 </div>
              </CardHeader>
              <CardContent className="p-4 space-y-2">
                 {activeCases.map((c) => (
                    <button 
                      key={c.id} 
                      onClick={() => setSelectedCase(c.id)}
                      className={cn(
                        "w-full text-left p-6 rounded-[2rem] border-2 transition-all group relative overflow-hidden",
                        selectedCase === c.id ? "bg-indigo-50 border-indigo-200 shadow-lg shadow-indigo-50" : "bg-white border-transparent hover:border-slate-100 hover:bg-slate-50"
                      )}
                    >
                       <div className="flex justify-between items-start">
                          <div className="space-y-1">
                             <p className="text-[10px] font-black uppercase text-indigo-400 tracking-widest">{c.id}</p>
                             <h4 className="text-lg font-black text-slate-900 group-hover:text-indigo-600 transition-colors">{c.patient}</h4>
                             <p className="text-xs font-bold text-slate-500">{c.type}</p>
                          </div>
                          <Badge className={cn(
                            "rounded-lg font-black text-[9px] uppercase border-none",
                            c.status === 'Shipped' ? "bg-emerald-100 text-emerald-600" : 
                            c.status === 'On Hold' ? "bg-red-100 text-red-600" : "bg-indigo-100 text-indigo-600"
                          )}>
                             {c.status}
                          </Badge>
                       </div>
                       <div className="mt-6 flex justify-between items-center">
                          <div className="flex items-center gap-2">
                             <Clock className="w-3 h-3 text-slate-400" />
                             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Due {c.dueDate}</span>
                          </div>
                          <Progress value={c.progress} className="h-1 w-20 bg-slate-100" />
                       </div>
                    </button>
                 ))}
              </CardContent>
           </Card>
        </div>

        {/* Right: Detailed Case View & Logistics (2/3) */}
        <div className="xl:col-span-2 space-y-8">
           {selectedCase ? (
              <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
                 <Card className="border-none shadow-[0_30px_80px_rgba(0,0,0,0.04)] rounded-[3rem] bg-white overflow-hidden">
                    <CardHeader className="p-10 pb-4 flex flex-row items-start justify-between">
                       <div className="flex gap-6 items-center">
                          <div className="w-20 h-20 rounded-[2rem] bg-indigo-600 flex items-center justify-center text-white shadow-xl shadow-indigo-100">
                             <Package className="w-10 h-10" />
                          </div>
                          <div>
                             <p className="text-[10px] font-black uppercase text-indigo-500 tracking-[0.2em]">Live Tracking Information</p>
                             <h2 className="text-3xl font-black text-slate-900 tracking-tight">Case {selectedCase}</h2>
                             <div className="flex items-center gap-4 mt-1">
                                <p className="text-sm font-bold text-slate-600 flex items-center gap-2 italic"><User className="w-4 h-4 text-slate-300" /> Olivia Chen</p>
                                <span className="text-slate-200">|</span>
                                <p className="text-sm font-bold text-slate-600 italic">Pioneer Dental Lab</p>
                             </div>
                          </div>
                       </div>
                       <div className="flex gap-2">
                          <Button variant="outline" className="rounded-xl h-12 px-6 font-bold border-slate-100 hover:bg-slate-50">Upload Photos</Button>
                          <Button className="rounded-xl h-12 px-6 bg-slate-900 hover:bg-slate-800 text-white font-black">Message Lab</Button>
                       </div>
                    </CardHeader>
                    <CardContent className="p-10 pt-10">
                       
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                          
                          {/* Timeline Section */}
                          <div className="space-y-8">
                             <h4 className="text-[10px] font-black uppercase text-slate-400 tracking-widest flex items-center gap-2">
                                <Clock className="w-3 h-3" /> Delivery Roadmap
                             </h4>
                             <div className="relative pl-6 space-y-6 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
                                {milestones.map((m, i) => (
                                   <div key={i} className="relative">
                                      <div className={cn(
                                        "absolute -left-[20px] top-1.5 w-3 h-3 rounded-full border-2 bg-white transition-all",
                                        m.completed ? "bg-indigo-600 border-indigo-600 scale-125 shadow-lg shadow-indigo-100" : "border-slate-200"
                                      )} />
                                      <div className="flex justify-between items-start">
                                         <div>
                                            <p className={cn("text-sm font-black", m.completed ? "text-slate-900" : "text-slate-300")}>{m.title}</p>
                                            {m.current && (
                                              <Badge className="bg-indigo-100 text-indigo-600 border-none font-black text-[8px] uppercase mt-1 py-0.5">Current Location</Badge>
                                            )}
                                         </div>
                                         <span className="text-[10px] font-bold text-slate-400">{m.date}</span>
                                      </div>
                                   </div>
                                ))}
                             </div>
                          </div>

                          {/* Logistics Action Section */}
                          <div className="space-y-8 bg-slate-50 p-8 rounded-[2.5rem] border border-slate-100">
                             <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                   <div className="p-3 rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-100">
                                      <Truck className="w-6 h-6" />
                                   </div>
                                   <div>
                                      <p className="text-[10px] font-black uppercase text-indigo-500 tracking-widest">Courier: UPS Second Day Air</p>
                                      <div className="flex items-center gap-2">
                                         <h4 className="text-xl font-black text-slate-900">In Transit</h4>
                                         <ArrowRight className="w-4 h-4 text-slate-400" />
                                         <h4 className="text-xl font-black text-slate-900">Arriving Friday</h4>
                                      </div>
                                   </div>
                                </div>
                                
                                <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3">
                                   <div className="flex justify-between items-center">
                                      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Tracking Number</span>
                                      <Button variant="ghost" className="h-6 px-2 text-[10px] font-black text-indigo-600 hover:bg-indigo-50">Copy</Button>
                                   </div>
                                   <p className="text-sm font-black text-slate-800 tracking-tight">1Z999AA10123456784</p>
                                   <Button className="w-full h-12 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 font-bold rounded-xl text-xs uppercase tracking-widest shadow-sm">
                                      <ExternalLink className="w-3 h-3 mr-2" /> View on UPS.com
                                   </Button>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                   <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-100 text-center">
                                      <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest">Est. Seating</p>
                                      <p className="text-sm font-black text-emerald-900 mt-1">Apr 12, 11:00</p>
                                   </div>
                                   <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 text-center">
                                      <p className="text-[9px] font-black text-blue-600 uppercase tracking-widest">Office Scan</p>
                                      <p className="text-sm font-black text-blue-900 mt-1">Pending Arrival</p>
                                   </div>
                                </div>

                                <div className="pt-6 border-t border-slate-200">
                                   <div className="flex justify-between items-center mb-4">
                                      <p className="text-xs font-black text-slate-900">Lab Profitability Analysis</p>
                                      <DollarSign className="w-4 h-4 text-emerald-500" />
                                   </div>
                                   <div className="grid grid-cols-2 gap-8">
                                      <div>
                                         <p className="text-[10px] font-bold text-slate-400 uppercase">Case Fee</p>
                                         <p className="text-base font-black text-slate-900">$245.00</p>
                                      </div>
                                      <div>
                                         <p className="text-[10px] font-bold text-slate-400 uppercase">Patient Total</p>
                                         <p className="text-base font-black text-slate-900">$1,450.00</p>
                                      </div>
                                   </div>
                                </div>
                             </div>
                          </div>

                       </div>

                    </CardContent>
                 </Card>
                 
                 {/* Financial Integration (Lab Invoices) */}
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden p-10 space-y-6">
                       <h4 className="text-lg font-black text-slate-900 flex items-center gap-3">
                          <FileText className="w-5 h-5 text-indigo-500" />
                          Lab Prescription Details
                       </h4>
                       <div className="space-y-4">
                          {[
                             { label: 'Prosthetic Type', value: 'High-Esthetic Zirconia' },
                             { label: 'Shade', value: 'A2 (VITA Pan)' },
                             { label: 'Gingival Shade', value: 'Standard Pink' },
                             { label: 'Margin Design', value: '360° Shoulder' },
                          ].map((item, i) => (
                             <div key={i} className="flex justify-between items-center py-3 border-b border-slate-50 last:border-0">
                                <span className="text-xs font-bold text-slate-400">{item.label}</span>
                                <span className="text-xs font-black text-slate-900">{item.value}</span>
                             </div>
                          ))}
                       </div>
                    </Card>

                    <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden p-10 space-y-6">
                       <div className="flex justify-between items-center">
                          <h4 className="text-lg font-black text-slate-900">Lab Communication</h4>
                          <Badge className="bg-indigo-600 text-white border-none font-bold">2 Unread</Badge>
                       </div>
                       <div className="space-y-4">
                          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 relative">
                             <div className="flex items-center gap-2 mb-2">
                                <p className="text-[10px] font-black text-indigo-600">Pioneer Dental Lab</p>
                                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">• 2h ago</span>
                             </div>
                             <p className="text-xs font-bold text-slate-600 leading-relaxed italic">"Received iTero scan. Quality is excellent. Beginning fabrication."</p>
                          </div>
                          <Button variant="ghost" className="w-full text-xs font-black text-slate-400 uppercase tracking-widest">View All Messages</Button>
                       </div>
                    </Card>
                 </div>
              </div>
           ) : (
              <div className="h-[600px] flex flex-col items-center justify-center text-slate-300 space-y-4 animate-in fade-in duration-1000">
                 <div className="w-20 h-20 rounded-[2rem] bg-slate-50 border-2 border-dashed border-slate-100 flex items-center justify-center">
                    <Microscope className="w-10 h-10 opacity-20" />
                 </div>
                 <p className="text-sm font-bold">Select a case from the list to view live tracking and fabrication details</p>
              </div>
           )}
        </div>

      </div>
    </div>
  );
}
