import { useState } from 'react';
import { 
  ImageIcon, 
  Maximize2, 
  Download, 
  Share2, 
  Plus, 
  Sun,
  Contrast,
  RotateCcw,
  Tag,
  Search,
  Zap,
  HardDrive
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
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

export default function ImagingHub() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [invert, setInvert] = useState(false);

  const imageSeries = [
    { id: 'SER-001', name: 'Bitewing Series (BWX)', count: 4, date: '2026-04-01' },
    { id: 'SER-012', name: 'Full Mouth Series (FMX)', count: 18, date: '2026-01-15' },
    { id: 'SER-045', name: 'Panoramic (Pan)', count: 1, date: '2026-01-15' },
  ];

  const recentImages = [
    { id: 'IMG-101', type: 'Bitewing', tooth: '18, 19', date: '2026-04-01', url: 'https://images.unsplash.com/photo-1542332606-b3d270b20165?auto=format&fit=crop&q=80&w=300' },
    { id: 'IMG-102', type: 'Periapical', tooth: '31', date: '2026-04-01', url: 'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&q=80&w=300' },
    { id: 'IMG-103', type: 'Panoramic', tooth: 'All', date: '2026-01-15', url: 'https://images.unsplash.com/photo-1590422998363-2283e3905f56?auto=format&fit=crop&q=80&w=300' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-[1600px] mx-auto animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6 border-slate-200">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight flex items-center gap-3">
             PACS & Imaging Hub
            <Badge variant="outline" className="bg-purple-50 text-purple-600 border-purple-100 font-bold uppercase tracking-widest text-[10px] py-1">DICOM v3.0</Badge>
          </h1>
          <p className="text-slate-500 font-medium mt-1">Unified diagnostic imaging with AI-enhanced contrast and hardware bridge.</p>
        </div>
        <div className="flex gap-3">
           <Button variant="outline" className="h-12 px-6 rounded-2xl font-bold border-slate-200 hover:bg-slate-50">
            <HardDrive className="w-4 h-4 mr-2" /> Capture TWAIN
          </Button>
          <Button className="h-12 px-8 rounded-2xl font-black bg-purple-600 hover:bg-purple-700 shadow-xl shadow-purple-100 transition-all hover:scale-[1.02] active:scale-95 text-white">
            <Plus className="w-4 h-4 mr-2" /> Import X-Rays
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8 h-full">
        <div className="xl:col-span-1 space-y-6">
           <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.03)] rounded-[2.5rem] bg-white overflow-hidden sticky top-8">
              <CardHeader className="p-8 pb-4">
                 <CardTitle className="text-xl font-black tracking-tight">Patient Library</CardTitle>
                 <div className="relative mt-4">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input className="w-full bg-slate-50 border-none rounded-xl h-10 pl-10 pr-4 text-sm font-bold placeholder:text-slate-400 focus:ring-2 focus:ring-purple-500/20 outline-none" placeholder="Search by tooth or ID..." />
                 </div>
              </CardHeader>
              <CardContent className="p-4 space-y-2">
                 <div className="px-4 space-y-4">
                    <div>
                       <h3 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3">Series</h3>
                       <div className="space-y-1">
                          {imageSeries.map(series => (
                             <button key={series.id} className="w-full text-left p-3 rounded-xl hover:bg-slate-50 group transition-all">
                                <p className="text-sm font-black text-slate-700 group-hover:text-purple-600">{series.name}</p>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{series.count} Images • {series.date}</p>
                             </button>
                          ))}
                       </div>
                    </div>
                    <Separator />
                    <div>
                       <h3 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3">Recent Singles</h3>
                       <div className="grid grid-cols-2 gap-3">
                          {recentImages.map(img => (
                             <button 
                               key={img.id} 
                               onClick={() => setSelectedImage(img.url)}
                               className={cn(
                                 "aspect-square rounded-2xl overflow-hidden border-2 transition-all relative group",
                                 selectedImage === img.url ? "border-purple-600 ring-4 ring-purple-100" : "border-slate-100 grayscale hover:grayscale-0"
                               )}
                             >
                                <img src={img.url} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                                <div className="absolute inset-x-0 bottom-0 p-2 bg-black/50 backdrop-blur-sm transform translate-y-full group-hover:translate-y-0 transition-transform">
                                   <p className="text-[8px] font-black text-white uppercase tracking-widest">Tooth {img.tooth}</p>
                                </div>
                             </button>
                          ))}
                       </div>
                    </div>
                 </div>
              </CardContent>
           </Card>
        </div>

        <div className="xl:col-span-2 space-y-6">
           <Card className="border-none shadow-[0_20px_80px_rgba(0,0,0,0.06)] rounded-[3rem] bg-black overflow-hidden relative min-h-[600px] flex flex-col">
              <div className="p-6 bg-slate-900 border-b border-white/5 flex justify-between items-center relative z-10">
                 <div className="flex gap-4">
                    <Button variant="ghost" className="text-slate-400 hover:text-white hover:bg-white/5 rounded-xl"><RotateCcw className="w-4 h-4" /></Button>
                    <Separator orientation="vertical" className="h-6 bg-white/10" />
                    <Button variant="ghost" className={cn("text-slate-400 hover:text-white hover:bg-white/5 rounded-xl", invert && "text-purple-400")} onClick={() => setInvert(!invert)}><Contrast className="w-4 h-4 mr-2" /> Pseudo-Invert</Button>
                 </div>
                 <div className="flex gap-2">
                    <Button size="sm" variant="ghost" className="text-slate-400 hover:text-white hover:bg-white/5 rounded-xl"><Tag className="w-4 h-4" /></Button>
                    <Button size="sm" variant="ghost" className="text-slate-400 hover:text-white hover:bg-white/5 rounded-xl"><Maximize2 className="w-4 h-4" /></Button>
                 </div>
              </div>

              <div className="flex-1 flex items-center justify-center p-12 relative overflow-hidden">
                 <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-800 to-black opacity-40 shrink-0" />
                 
                 {selectedImage ? (
                    <div 
                      className="relative z-10 shadow-[0_0_100px_rgba(0,0,0,0.5)] transition-all duration-300 rounded-lg overflow-hidden"
                      style={{ 
                        filter: `brightness(${brightness}%) contrast(${contrast}%) ${invert ? 'invert(1)' : ''}`,
                        maxWidth: '90%',
                        maxHeight: '100%'
                      }}
                    >
                       <img src={selectedImage} alt="PACS Viewer" className="max-w-full h-auto shadow-2xl" />
                       <div className="absolute top-1/4 left-1/3 w-20 h-20 border-2 border-dashed border-red-500 rounded-lg animate-pulse">
                          <span className="absolute -top-6 left-0 bg-red-600 text-white text-[8px] font-black px-1 py-0.5 rounded uppercase tracking-widest whitespace-nowrap">Distal Decay Path</span>
                       </div>
                    </div>
                 ) : (
                    <div className="flex flex-col items-center justify-center text-slate-600 space-y-6 relative z-10 animate-in fade-in duration-1000">
                       <div className="w-24 h-24 rounded-[2rem] bg-white/5 border border-white/10 flex items-center justify-center">
                          <ImageIcon className="w-10 h-10 opacity-20" />
                       </div>
                       <p className="text-sm font-bold tracking-tight">Select an image from library to view diagnostics</p>
                    </div>
                 )}
                 
                 <div className="absolute bottom-6 right-6 text-right space-y-0.5 opacity-40 pointer-events-none">
                    <p className="text-[10px] font-black text-white uppercase tracking-widest">DICOM UID: 1.2.840.10008.5.1</p>
                    <p className="text-[10px] font-bold text-white/50 uppercase">kVp: 70 • mA: 8 • s: 0.12</p>
                 </div>
              </div>

              <div className="p-8 bg-slate-950 border-t border-white/5 relative z-10">
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                    <div className="space-y-4">
                       <div className="flex justify-between items-center">
                          <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2"><Sun className="w-3 h-3" /> Brightness</label>
                          <span className="text-[10px] font-black text-white">{brightness}%</span>
                       </div>
                       <Slider value={[brightness]} onValueChange={([val]) => setBrightness(val)} max={200} step={1} className="py-2" />
                    </div>
                    <div className="space-y-4">
                       <div className="flex justify-between items-center">
                          <label className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2"><Contrast className="w-3 h-3" /> Contrast</label>
                          <span className="text-[10px] font-black text-white">{contrast}%</span>
                       </div>
                       <Slider value={[contrast]} onValueChange={([val]) => setContrast(val)} max={200} step={1} className="py-2" />
                    </div>
                 </div>
              </div>
           </Card>
        </div>

        <div className="xl:col-span-1 space-y-6">
           <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.04)] rounded-[2.5rem] bg-white overflow-hidden">
              <CardHeader className="p-10 pb-0">
                 <CardTitle className="text-xl font-black tracking-tight text-slate-800">Visual Insights</CardTitle>
                 <CardDescription className="font-bold text-slate-400 uppercase text-[10px] tracking-widest text-wrap">AI-Driven Image Analysis</CardDescription>
              </CardHeader>
              <CardContent className="p-10 space-y-8">
                 <div className="p-6 rounded-[2rem] bg-purple-50 border border-purple-100 space-y-4">
                    <div className="flex items-center gap-3">
                       <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white">
                          <Zap className="w-4 h-4" />
                       </div>
                       <p className="text-sm font-black text-purple-900">Periapical Anomaly Detected</p>
                    </div>
                    <p className="text-xs font-bold text-purple-700/70 leading-relaxed italic">
                       "Automatic bone level measurement suggests 3.2mm loss on tooth 31 distal."
                    </p>
                    <Button className="w-full bg-white text-purple-600 hover:bg-white/90 font-black h-10 rounded-xl shadow-sm border border-purple-200">Review AI Findings</Button>
                 </div>
                 
                 <div className="space-y-6">
                    <h3 className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Image History</h3>
                    {[
                      { type: 'Sharing', details: 'Sent to Patient Portal', date: '5m ago' },
                      { type: 'Annotation', details: 'Added measurement by Dr. Smith', date: '2h ago' },
                      { type: 'Acquisition', details: 'Captured via DEXIS Sensor', date: '4h ago' },
                    ].map((activity, idx) => (
                      <div key={idx} className="flex gap-3">
                         <div className="w-1.5 h-1.5 rounded-full bg-purple-600 mt-2 shrink-0" />
                         <div>
                            <p className="text-sm font-black text-slate-800">{activity.type}</p>
                            <p className="text-xs font-bold text-slate-500">{activity.details}</p>
                            <p className="text-[9px] font-bold text-slate-400 uppercase mt-1 tracking-widest">{activity.date}</p>
                         </div>
                      </div>
                    ))}
                 </div>

                 <div className="pt-6 border-t border-slate-100 flex gap-4">
                    <Button className="flex-1 h-12 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 shadow-sm text-slate-900 font-bold group">
                       <Share2 className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" /> Refer
                    </Button>
                    <Button className="flex-1 h-12 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 shadow-sm text-slate-900 font-bold group">
                       <Download className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" /> Save
                    </Button>
                 </div>
              </CardContent>
           </Card>
        </div>

      </div>
    </div>
  );
}

function Separator({ className, orientation = 'horizontal' }: { className?: string, orientation?: 'horizontal' | 'vertical' }) {
  return (
    <div className={cn(
      "bg-slate-100 shrink-0", 
      orientation === 'horizontal' ? "h-px w-full" : "w-px h-full",
      className
    )} />
  );
}
