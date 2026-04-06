import { 
  Inbox, 
  Send, 
  Search, 
  Plus, 
  Building2, 
  User, 
  Clock, 
  MoreVertical,
  ArrowRightLeft,
  Sparkles,
  Zap
} from 'lucide-react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function ReferralHub() {
  const incomingReferrals = [
    { 
      id: 'REF-8891', 
      patient: 'Sarah Miller', 
      from: 'Downtown Seattle Branch', 
      type: 'Endodontics', 
      status: 'Pending', 
      urgent: true, 
      date: '2026-04-05',
      note: 'Calcified canal on #14. Requires specialist microscope.'
    },
    { 
      id: 'REF-8885', 
      patient: 'James Wilson', 
      from: 'Bellevue Plaza', 
      type: 'Oral Surgery', 
      status: 'Scheduled', 
      urgent: false, 
      date: '2026-04-02',
      note: 'Impacted #17, #32'
    },
  ];

  return (
    <div className="p-10 space-y-10 max-w-[1500px] mx-auto animate-in fade-in duration-700">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b pb-8 border-slate-100">
        <div className="space-y-1">
          <h1 className="text-4xl font-black text-slate-900 tracking-tight flex items-center gap-3">
             <ArrowRightLeft className="w-8 h-8 text-blue-600" />
             Inter-Practice Referral Hub
          </h1>
          <p className="text-slate-500 font-medium">Seamlessly share patients and clinical diagnostics between branch locations.</p>
        </div>
        <div className="flex gap-3">
           <Button variant="outline" className="h-12 px-6 rounded-2xl font-bold border-slate-200 hover:bg-slate-50">
            <Inbox className="w-4 h-4 mr-2" /> Global Inbox
          </Button>
          <Button className="h-12 px-8 rounded-2xl font-black bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all hover:scale-[1.02] active:scale-95 text-white">
            <Plus className="w-4 h-4 mr-2" /> Create Internal Referral
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left: Summary Cards & Filters (1/4) */}
        <div className="lg:col-span-1 space-y-6">
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden">
              <CardHeader className="p-8 pb-4">
                 <CardTitle className="text-xl font-black tracking-tight">Referral Status</CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-1">
                 <button className="w-full h-14 rounded-2xl bg-blue-50 text-blue-700 flex items-center justify-between px-6 font-bold group">
                    <div className="flex items-center gap-3">
                       <Inbox className="w-5 h-5" />
                       Incoming New
                    </div>
                    <Badge className="bg-blue-600 text-white border-none font-black text-[10px]">12</Badge>
                 </button>
                 <button className="w-full h-14 rounded-2xl hover:bg-slate-50 text-slate-600 flex items-center justify-between px-6 font-bold group transition-all">
                    <div className="flex items-center gap-3">
                       <Send className="w-5 h-5 text-slate-300 group-hover:text-slate-600" />
                       Outgoing Sent
                    </div>
                    <span className="text-xs font-bold text-slate-400">45</span>
                 </button>
                 <button className="w-full h-14 rounded-2xl hover:bg-slate-50 text-slate-600 flex items-center justify-between px-6 font-bold group transition-all">
                    <div className="flex items-center gap-3">
                       <Clock className="w-5 h-5 text-slate-300 group-hover:text-slate-600" />
                       Action Required
                    </div>
                    <Badge className="bg-amber-100 text-amber-600 border-none font-black text-[10px]">2</Badge>
                 </button>
              </CardContent>
           </Card>

           <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-slate-900 text-white overflow-hidden">
              <CardContent className="p-8 space-y-6">
                 <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-blue-400">
                       <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                       <p className="text-sm font-black">Smart Matching</p>
                       <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Enterprise Feature</p>
                    </div>
                 </div>
                 <p className="text-xs font-bold leading-relaxed text-white/60">
                    Your group has <strong>3 Oral Surgeons</strong> with availability in the next 48 hours for emergency referrals.
                 </p>
                 <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-black h-12 rounded-xl">Check Global Availability</Button>
              </CardContent>
           </Card>
        </div>

        {/* Center: Main Referral Inbox (3/4) */}
        <div className="lg:col-span-3 space-y-6">
           <Tabs defaultValue="incoming" className="w-full">
              <div className="flex justify-between items-center mb-6">
                 <TabsList className="bg-slate-100 p-1.5 rounded-2xl h-14 border border-slate-200">
                    <TabsTrigger value="incoming" className="rounded-xl px-8 font-black text-sm data-[state=active]:bg-white data-[state=active]:shadow-xl data-[state=active]:text-blue-600 transition-all">Incoming</TabsTrigger>
                    <TabsTrigger value="outgoing" className="rounded-xl px-8 font-black text-sm data-[state=active]:bg-white data-[state=active]:shadow-xl data-[state=active]:text-blue-600 transition-all">Outgoing</TabsTrigger>
                    <TabsTrigger value="referrals_list" className="rounded-xl px-8 font-black text-sm data-[state=active]:bg-white data-[state=active]:shadow-xl data-[state=active]:text-blue-600 transition-all">All History</TabsTrigger>
                 </TabsList>
                 <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input className="bg-slate-100 border-none rounded-2xl h-14 pl-12 pr-6 text-sm font-bold min-w-[300px] outline-none focus:ring-2 focus:ring-blue-600/20" placeholder="Search patients..." />
                 </div>
              </div>

              <TabsContent value="incoming" className="space-y-4 m-0">
                 {incomingReferrals.map((ref) => (
                    <Card key={ref.id} className="border border-slate-100 shadow-[0_10px_40px_rgba(0,0,0,0.02)] rounded-[2rem] bg-white overflow-hidden hover:border-blue-200 transition-all group">
                       <CardContent className="p-8">
                          <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
                             <div className="flex items-center gap-4">
                                <div className="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 group-hover:scale-105 transition-transform">
                                   <User className="w-6 h-6" />
                                </div>
                                <div>
                                   <div className="flex items-center gap-3">
                                      <h3 className="text-lg font-black text-slate-900 tracking-tight">{ref.patient}</h3>
                                      {ref.urgent && <Badge className="bg-red-500 text-white border-none font-black animate-pulse uppercase text-[8px] py-0.5">Urgent</Badge>}
                                   </div>
                                   <div className="flex items-center gap-4 mt-1">
                                      <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest flex items-center gap-1.5"><Building2 className="w-3 h-3" /> {ref.from}</p>
                                      <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest flex items-center gap-1.5"><Zap className="w-3 h-3" /> {ref.type}</p>
                                   </div>
                                </div>
                             </div>

                             <div className="flex-1 max-w-md">
                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                   <p className="text-xs font-bold text-slate-600 leading-relaxed truncate group-hover:text-wrap">
                                      <span className="font-black text-slate-400 mr-2 italic">Ref Note:</span>
                                      {ref.note}
                                   </p>
                                </div>
                             </div>

                             <div className="flex items-center gap-6">
                                <div className="text-right">
                                   <p className="text-xs font-black text-slate-900 italic">#{ref.id}</p>
                                   <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1">{ref.date}</p>
                                </div>
                                <div className="flex gap-2">
                                   <Button variant="outline" className="h-10 rounded-xl border-slate-200 font-bold hover:bg-slate-50">View Case</Button>
                                   <Button className="h-10 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-black px-6">Schedule</Button>
                                   <Button variant="ghost" className="h-10 w-10 p-0 rounded-xl text-slate-400 hover:text-slate-800"><MoreVertical className="w-4 h-4" /></Button>
                                </div>
                             </div>
                          </div>
                       </CardContent>
                    </Card>
                 ))}

                 <div className="p-12 border-2 border-dashed border-slate-100 rounded-[2.5rem] flex flex-col items-center justify-center text-center space-y-4">
                    <div className="w-16 h-16 rounded-[2rem] bg-slate-50 flex items-center justify-center text-slate-200">
                       <Inbox className="w-8 h-8" />
                    </div>
                    <div>
                       <p className="text-sm font-black text-slate-400">End of Inbox</p>
                       <p className="text-xs font-bold text-slate-300">You are all caught up with internal referrals.</p>
                    </div>
                 </div>
              </TabsContent>
           </Tabs>
        </div>

      </div>
    </div>
  );
}
