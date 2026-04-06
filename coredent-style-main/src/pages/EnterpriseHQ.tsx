import { 
  Building2, 
  Users, 
  TrendingUp, 
  DollarSign, 
  LayoutDashboard, 
  BarChart3, 
  ArrowUpRight, 
  ArrowDownRight, 
  Globe, 
  Sparkles, 
  Zap,
  ChevronRight
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
import { cn } from '@/lib/utils';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell, 
  AreaChart,
  Area
} from 'recharts';

export default function EnterpriseHQ() {

  const kpis = [
    { title: 'Consolidated Production', value: '$842,500', trend: '+12.5%', icon: TrendingUp, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { title: 'Group Collections', value: '$795,200', trend: '+8.2%', icon: DollarSign, color: 'text-blue-600', bg: 'bg-blue-50' },
    { title: 'Total New Patients', value: '342', trend: '+15.4%', icon: Users, color: 'text-purple-600', bg: 'bg-purple-50' },
    { title: 'Avg. Utilization', value: '88.4%', trend: '-2.1%', icon: BarChart3, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  const branchData = [
    { name: 'Downtown Seattle', prod: 245000, coll: 232000, patients: 84, util: 92, color: '#10b981' },
    { name: 'Bellevue Plaza', prod: 212000, coll: 198000, patients: 92, util: 87, color: '#3b82f6' },
    { name: 'Capitol Hill', prod: 185000, coll: 172000, patients: 65, util: 84, color: '#f59e0b' },
    { name: 'Redmond Way', prod: 156000, coll: 145000, patients: 78, util: 91, color: '#8b5cf6' },
    { name: 'Issaquah Highlands', prod: 44500, coll: 48200, patients: 23, util: 78, color: '#ec4899' },
  ];

  const trendData = [
    { month: 'Oct', prod: 620000 },
    { month: 'Nov', prod: 680000 },
    { month: 'Dec', prod: 740000 },
    { month: 'Jan', prod: 710000 },
    { month: 'Feb', prod: 790000 },
    { month: 'Mar', prod: 842500 },
  ];

  return (
    <div className="p-8 space-y-10 max-w-[1700px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-1000">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-b pb-8 border-slate-200">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
             <div className="w-12 h-12 rounded-2xl bg-slate-900 flex items-center justify-center text-white shadow-xl shadow-slate-200">
                <Globe className="w-6 h-6" />
             </div>
             <div>
                <h1 className="text-4xl font-black text-slate-900 tracking-tight">Enterprise HQ Dashboard</h1>
                <p className="text-slate-500 font-bold uppercase text-[10px] tracking-[0.2em]">Pacific Dental Group • Real-Time Consolidated Analytics</p>
             </div>
          </div>
        </div>
        <div className="flex gap-4">
           <Button variant="outline" className="h-12 px-6 rounded-2xl font-bold border-slate-200 hover:bg-slate-50">
             <LayoutDashboard className="w-4 h-4 mr-2" /> Global Settings
           </Button>
           <Button className="h-12 px-8 rounded-2xl font-black bg-slate-900 hover:bg-slate-800 shadow-2xl transition-all hover:scale-[1.02] active:scale-95 text-white">
             <ArrowUpRight className="w-4 h-4 mr-2" /> Download Q1 Report
           </Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((kpi, idx) => (
           <Card key={idx} className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden group hover:shadow-[0_25px_60px_rgba(0,0,0,0.06)] transition-all">
              <CardContent className="p-8">
                 <div className="flex justify-between items-start">
                    <div className={cn("p-3 rounded-2xl", kpi.bg)}>
                       <kpi.icon className={cn("w-6 h-6", kpi.color)} />
                    </div>
                    <Badge className={cn("bg-transparent border-none font-black text-[10px]", kpi.trend.startsWith('+') ? "text-emerald-500" : "text-amber-500")}>
                       {kpi.trend} {kpi.trend.startsWith('+') ? <ArrowUpRight className="w-3 h-3 ml-1" /> : <ArrowDownRight className="w-3 h-3 ml-1" />}
                    </Badge>
                 </div>
                 <div className="mt-6">
                    <p className="text-slate-400 font-bold uppercase text-[9px] tracking-widest">{kpi.title}</p>
                    <h3 className="text-3xl font-black text-slate-900 mt-1">{kpi.value}</h3>
                 </div>
              </CardContent>
           </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* Left: Production Benchmark (2/3) */}
        <div className="xl:col-span-2 space-y-8">
           <Card className="border-none shadow-[0_30px_90px_rgba(0,0,0,0.05)] rounded-[3rem] bg-white overflow-hidden">
              <CardHeader className="p-10 pb-4">
                 <CardTitle className="text-2xl font-black tracking-tight text-slate-900 flex items-center justify-between">
                    Location Comparison
                    <div className="flex gap-2">
                       <Badge variant="outline" className="h-8 px-4 font-bold border-slate-100 bg-slate-50 text-slate-600">This Month</Badge>
                       <Badge variant="outline" className="h-8 px-4 font-bold border-slate-100 bg-white text-slate-400">vs Last Month</Badge>
                    </div>
                 </CardTitle>
                 <CardDescription className="font-bold text-slate-400 uppercase text-[10px] tracking-widest">Monthly Gross Production Across 5 Branches</CardDescription>
              </CardHeader>
              <CardContent className="p-10 pt-4 h-[440px]">
                 <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={branchData} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
                       <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                       <XAxis 
                         dataKey="name" 
                         axisLine={false} 
                         tickLine={false} 
                         tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 800 }} 
                         dy={20}
                        />
                       <YAxis 
                         axisLine={false} 
                         tickLine={false} 
                         tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 800 }} 
                         tickFormatter={(val) => `$${val/1000}k`} 
                       />
                       <Tooltip 
                         contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 20px 50px rgba(0,0,0,0.1)', padding: '20px' }}
                         cursor={{ fill: '#f8fafc', radius: 16 }}
                       />
                       <Bar dataKey="prod" radius={[12, 12, 12, 12]} barSize={50}>
                          {branchData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.8} />
                          ))}
                       </Bar>
                    </BarChart>
                 </ResponsiveContainer>
              </CardContent>
           </Card>

           {/* Location Performance Matrix */}
           <Card className="border-none shadow-[0_30px_90px_rgba(0,0,0,0.05)] rounded-[3rem] bg-white overflow-hidden">
              <CardHeader className="p-10 pb-0">
                 <CardTitle className="text-2xl font-black tracking-tight">Performance Matrix</CardTitle>
              </CardHeader>
              <CardContent className="p-10">
                 <div className="space-y-4">
                    <div className="grid grid-cols-6 items-center px-4 py-2 border-b border-slate-50 text-[10px] font-black uppercase tracking-widest text-slate-400">
                       <div className="col-span-2">Practice Name</div>
                       <div className="text-center">Util %</div>
                       <div className="text-center">New Pts</div>
                       <div className="text-right">Net Prod</div>
                       <div className="text-right">Status</div>
                    </div>
                    {branchData.map((branch, i) => (
                       <div key={i} className="grid grid-cols-6 items-center px-4 py-6 rounded-2xl hover:bg-slate-50 transition-colors group">
                          <div className="col-span-2 flex items-center gap-4">
                             <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-[10px] font-black" style={{ backgroundColor: branch.color }}>
                                {branch.name.charAt(0)}
                             </div>
                             <p className="text-sm font-black text-slate-800">{branch.name}</p>
                          </div>
                          <div className="flex flex-col items-center">
                             <span className="text-sm font-black text-slate-900">{branch.util}%</span>
                             <Progress value={branch.util} className="h-1 w-12 mt-2 bg-slate-100" />
                          </div>
                          <div className="text-center">
                             <span className="text-sm font-black text-slate-900">{branch.patients}</span>
                          </div>
                          <div className="text-right">
                             <span className="text-sm font-black text-slate-900">${(branch.prod / 1000).toFixed(1)}k</span>
                          </div>
                          <div className="text-right">
                             <Badge className={cn(
                               "rounded-lg font-black text-[9px] uppercase",
                               branch.util > 90 ? "bg-emerald-100 text-emerald-600" : "bg-amber-100 text-amber-600"
                             )}>
                                {branch.util > 90 ? "Optimal" : "Slack Detected"}
                             </Badge>
                          </div>
                       </div>
                    ))}
                 </div>
              </CardContent>
           </Card>
        </div>

        {/* Right: Operational Insights (1/3) */}
        <div className="xl:col-span-1 space-y-8">
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.06)] rounded-[3rem] bg-slate-900 text-white overflow-hidden">
              <CardHeader className="p-10 pb-4">
                 <CardTitle className="text-2xl font-black tracking-tight flex items-center gap-3">
                    <Sparkles className="w-6 h-6 text-indigo-400" /> Enterprise Pulse
                 </CardTitle>
                 <CardDescription className="text-slate-500 font-bold uppercase text-[10px] tracking-widest">Autonomous Global Overview</CardDescription>
              </CardHeader>
              <CardContent className="p-10 pt-4 space-y-8">
                 
                 <div className="p-6 rounded-[2rem] bg-white/5 border border-white/10 space-y-4">
                    <div className="flex justify-between items-start">
                       <div>
                          <p className="text-[10px] font-black uppercase text-indigo-400 tracking-widest">Group Trend</p>
                          <h4 className="text-2xl font-black mt-1">$842.5k</h4>
                       </div>
                       <Badge className="bg-emerald-500 text-white border-none font-bold">+18.4% YoY</Badge>
                    </div>
                    <div className="h-24 w-full">
                       <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={trendData}>
                             <defs>
                                <linearGradient id="colorProd" x1="0" y1="0" x2="0" y2="1">
                                   <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3}/>
                                   <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                                </linearGradient>
                             </defs>
                             <Area type="monotone" dataKey="prod" stroke="#818cf8" strokeWidth={3} fillOpacity={1} fill="url(#colorProd)" />
                          </AreaChart>
                       </ResponsiveContainer>
                    </div>
                 </div>

                 <div className="space-y-6">
                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Strategic Action Items</h3>
                    <div className="space-y-4">
                       <div className="flex items-center gap-4 group cursor-pointer">
                          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
                             <Zap className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                             <p className="text-sm font-black">Rebalance Issaquah Hygine</p>
                             <p className="text-[10px] font-bold text-slate-500 uppercase">Utilization at 78% (Group avg 88%)</p>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-700" />
                       </div>
                       <div className="flex items-center gap-4 group cursor-pointer">
                          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-500 group-hover:text-white transition-all">
                             <TrendingUp className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                             <p className="text-sm font-black">Increase Bellevue Perio Fee</p>
                             <p className="text-[10px] font-bold text-slate-500 uppercase">Competitive deficit detected vs Redmond</p>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-700" />
                       </div>
                    </div>
                 </div>

                 <Button className="w-full h-14 rounded-2xl bg-white text-slate-900 hover:bg-slate-100 font-black tracking-tight text-lg shadow-xl">
                    Launch Consolidated Admin
                 </Button>

              </CardContent>
           </Card>
           
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden p-8 flex items-center justify-between">
              <div className="flex items-center gap-4">
                 <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                    <Building2 className="w-5 h-5" />
                 </div>
                 <div>
                    <p className="text-sm font-black text-slate-900">Enterprise Map View</p>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active Locations: 11 Regional</p>
                 </div>
              </div>
              <Button size="sm" variant="ghost" className="rounded-full text-slate-400"><ChevronRight className="w-4 h-4" /></Button>
           </Card>
        </div>

      </div>
    </div>
  );
}
