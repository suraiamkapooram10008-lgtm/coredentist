import { useState } from 'react';
import { 
  Mic, 
  Brain, 
  Sparkles, 
  Scan, 
  CheckCircle2, 
  Square,
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

interface AIClinicalAssistantProps {
  onApplyFinding: (toothNumber: number, finding: string) => void;
}

export function AIClinicalAssistant({ onApplyFinding }: AIClinicalAssistantProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [findings, setFindings] = useState<{
    id: string;
    tooth: number;
    description: string;
    certainty: number;
    status: 'detected' | 'applied';
  }[]>([]);

  // Mock Findings Generation
  const mockAICall = () => {
    setIsListening(false);
    setIsProcessing(true);
    
    setTimeout(() => {
      const newFinding = {
        id: Math.random().toString(36).substr(2, 9),
        tooth: Math.floor(Math.random() * 32) + 1,
        description: 'Possible Class II Decay (Distal)',
        certainty: 88,
        status: 'detected' as const
      };
      setFindings(prev => [newFinding, ...prev]);
      setIsProcessing(false);
      setTranscription('');
    }, 1500);
  };

  const toggleListening = () => {
    if (isListening) {
      mockAICall();
    } else {
      setIsListening(true);
      setTranscription('Patient presenting with sensitivity on upper right...');
    }
  };

  return (
    <Card className="border-none shadow-[0_20px_60px_rgba(0,0,0,0.06)] rounded-[2.5rem] bg-slate-900 text-white overflow-hidden">
      <CardHeader className="p-8 pb-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-2xl bg-blue-500/20 flex items-center justify-center text-blue-400 border border-blue-500/20">
                <Brain className="w-6 h-6" />
             </div>
             <div>
                <CardTitle className="text-lg font-black tracking-tight">AI Clinical Assistant</CardTitle>
                <CardDescription className="text-slate-400 font-bold uppercase text-[9px] tracking-widest">Enhanced Diagnostics v4.2</CardDescription>
             </div>
          </div>
          <Badge className="bg-blue-600 text-white border-none animate-pulse">Live Analysis</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-8 pt-4 space-y-6">
        
        {/* Voice Interaction HUD */}
        <div className="p-6 rounded-[2rem] bg-white/5 border border-white/10 relative overflow-hidden group">
           <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity" />
           
           <div className="flex items-center justify-between relative z-10">
              <div className="space-y-1">
                 <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Voice Transcription</p>
                 <p className={cn(
                    "text-sm font-medium transition-all duration-500",
                    isListening ? "text-blue-400" : "text-slate-400 italic"
                 )}>
                    {isListening ? transcription : 'Click microphone to start voice-charting...'}
                 </p>
              </div>
              <Button 
                onClick={toggleListening}
                className={cn(
                  "w-14 h-14 rounded-2xl transition-all duration-500 shadow-2xl",
                  isListening 
                    ? "bg-red-500 hover:bg-red-600 scale-110 shadow-red-500/20" 
                    : "bg-blue-600 hover:bg-blue-700 shadow-blue-600/20"
                )}
              >
                {isListening ? <Square className="w-6 h-6 fill-current" /> : <Mic className="w-6 h-6" />}
              </Button>
           </div>
           
           {isListening && (
              <div className="mt-4 flex gap-1 h-3 items-center">
                 {[...Array(12)].map((_, i) => (
                    <div 
                      key={i} 
                      className="flex-1 bg-blue-400 rounded-full animate-bounce" 
                      style={{ 
                        animationDelay: `${i * 0.1}s`,
                        height: `${Math.random() * 100 + 20}%`
                      }} 
                    />
                 ))}
              </div>
           )}
        </div>

        {/* AI Processing Status */}
        {isProcessing && (
           <div className="space-y-3 animate-in fade-in slide-in-from-top-2">
              <div className="flex justify-between items-end">
                 <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Cross-referencing radiographic data...
                 </span>
                 <span className="text-[10px] font-black">75%</span>
              </div>
              <Progress value={75} className="h-1 bg-white/5" />
           </div>
        )}

        {/* Findings List */}
        <div className="space-y-4">
           <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest">Detected Findings</h3>
           {findings.length === 0 ? (
              <div className="p-8 rounded-[1.5rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center space-y-3">
                 <Scan className="w-8 h-8 text-slate-700" />
                 <p className="text-xs font-bold text-slate-600">No autonomous findings detected.<br/>Start voice capture or upload X-rays.</p>
              </div>
           ) : (
              <div className="space-y-3 max-h-[240px] overflow-y-auto pr-2 custom-scrollbar">
                 {findings.map((finding) => (
                    <div 
                      key={finding.id} 
                      className={cn(
                        "p-4 rounded-2xl border transition-all flex items-center justify-between",
                        finding.status === 'applied' 
                          ? "bg-emerald-500/10 border-emerald-500/20" 
                          : "bg-white/5 border-white/10 hover:border-blue-500/30"
                      )}
                    >
                       <div className="flex items-center gap-3">
                          <div className={cn(
                            "w-8 h-8 rounded-xl flex items-center justify-center text-[10px] font-black",
                            finding.status === 'applied' ? "bg-emerald-500 text-white" : "bg-blue-600 text-white"
                          )}>
                             #{finding.tooth}
                          </div>
                          <div>
                             <p className="text-sm font-black text-white">{finding.description}</p>
                             <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{finding.certainty}% Accuracy Confidence</p>
                          </div>
                       </div>
                       <Button 
                         size="sm" 
                         variant="ghost" 
                         className="h-8 w-8 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
                         onClick={() => {
                            onApplyFinding(finding.tooth, finding.description);
                            setFindings(prev => prev.map(f => f.id === finding.id ? { ...f, status: 'applied' } : f));
                         }}
                         disabled={finding.status === 'applied'}
                       >
                          {finding.status === 'applied' ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <ChevronRight className="w-4 h-4" />}
                       </Button>
                    </div>
                 ))}
              </div>
           )}
        </div>

        <div className="pt-4 border-t border-white/10 flex items-center justify-between">
           <div className="flex -space-x-2">
              {[1, 2, 3].map(i => (
                 <div key={i} className="w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center">
                    <Sparkles className="w-3 h-3 text-blue-400" />
                 </div>
              ))}
           </div>
           <Button variant="link" className="text-blue-400 font-black text-[10px] uppercase tracking-widest h-auto p-0">Detailed Clinical Report</Button>
        </div>

      </CardContent>
    </Card>
  );
}

function RefreshCw({ className }: { className?: string }) {
  return (
    <svg 
      className={className}
      xmlns="http://www.w3.org/2000/svg" 
      width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    >
      <path d="M3 12a9 9 0 1 1 9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 11V3"/><path d="M7 3H3"/>
    </svg>
  );
}
