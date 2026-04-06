import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  CheckCircle2, 
  Mail, 
  ArrowLeft, 
  ExternalLink,
  ShieldCheck,
  Star
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function BookingSuccess() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      {/* Decorative background */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-20 overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-400 blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-300 blur-[120px] animate-pulse" />
      </div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-2xl"
      >
        <Card className="border-none shadow-[0_30px_70px_rgba(0,0,0,0.08)] bg-white/90 backdrop-blur-xl rounded-[2.5rem] overflow-hidden">
          <CardContent className="p-12 text-center space-y-10">
            {/* Success Icon */}
            <div className="flex justify-center">
              <div className="relative">
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                  className="w-24 h-24 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-2xl shadow-emerald-200"
                >
                  <CheckCircle2 className="w-12 h-12" />
                </motion.div>
                <motion.div 
                  animate={{ rotate: 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                  className="absolute inset-[-10px] border-2 border-dashed border-emerald-200 rounded-full"
                />
              </div>
            </div>

            {/* Content */}
            <div className="space-y-4">
              <h1 className="text-4xl font-black text-slate-800 tracking-tight">Booking Requested!</h1>
              <p className="text-slate-500 text-lg max-w-md mx-auto">
                Thank you for choosing <span className="font-bold text-slate-900">CoreDent Family Dental</span>. 
                We have received your request and will review it shortly.
              </p>
            </div>

            {/* Meta Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="bg-slate-50 p-6 rounded-2xl flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 shrink-0">
                  <Mail className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-black uppercase text-slate-400 tracking-widest">Next Steps</p>
                  <p className="text-sm font-bold text-slate-700 leading-snug">Check your email for a summary of your request.</p>
                </div>
              </div>
              <div className="bg-slate-50 p-6 rounded-2xl flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-black uppercase text-slate-400 tracking-widest">Confirmation</p>
                  <p className="text-sm font-bold text-slate-700 leading-snug">A staff member will contact you to confirm the time.</p>
                </div>
              </div>
            </div>

            <div className="pt-4 space-y-6">
              <div className="flex flex-col md:flex-row gap-4 justify-center">
                <Button 
                  onClick={() => navigate('/')} 
                  variant="outline" 
                  className="h-14 px-8 rounded-2xl border-none bg-slate-100 hover:bg-slate-200 text-slate-700 font-black transition-all"
                >
                  <ArrowLeft className="w-5 h-5 mr-2" /> Return Home
                </Button>
                <Button 
                  className="h-14 px-10 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-black shadow-xl shadow-blue-100 transition-all hover:scale-105 active:scale-95"
                >
                  Add to Calendar <ExternalLink className="w-5 h-5 ml-2" />
                </Button>
              </div>

              <div className="flex items-center justify-center gap-2 text-slate-400">
                <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                <span className="text-[10px] font-black uppercase tracking-widest leading-none">Trust Center Verified Booking</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
