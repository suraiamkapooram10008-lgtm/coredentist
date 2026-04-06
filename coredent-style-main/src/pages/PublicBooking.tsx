import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, 
  Clock, 
  User, 
  Phone, 
  Mail, 
  ChevronRight, 
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Stethoscope,
  Info,
  ArrowRight
} from 'lucide-react';
import { format, addDays, startOfToday, isSameDay } from 'date-fns';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { toast } from '@/components/ui/use-toast';
import { PageLoader } from '@/components/ui/spinner';

// --- Types ---
interface BookingPage {
  page_slug: string;
  page_title: string;
  welcome_message?: string;
  logo_url?: string;
  primary_color?: string;
  background_image_url?: string;
  allow_new_patients: boolean;
  allow_existing_patients: boolean;
  booking_window_days: number;
  min_notice_hours: number;
  business_hours: any;
  intake_form_fields: any[];
}

interface TimeSlot {
  start_time: string;
  end_time: string;
  is_available: boolean;
}

// --- Mock Data / API Helpers ---
const fetchPublicPage = async (slug: string): Promise<BookingPage> => {
  // In production, this would be: await api.get(`/booking/public/${slug}`)
  // For now, returning a mock based on the backend model
  return {
    page_slug: slug,
    page_title: "CoreDent Family Dental",
    welcome_message: "Welcome to our online booking portal. Please select a service and time that works best for you.",
    logo_url: "https://images.unsplash.com/photo-1606811841660-1b5168c5c918?auto=format&fit=crop&q=80&w=200&h=200",
    primary_color: "#1d4ed8",
    allow_new_patients: true,
    allow_existing_patients: true,
    booking_window_days: 90,
    min_notice_hours: 24,
    business_hours: {},
    intake_form_fields: []
  };
};

const STEPS = [
  { id: 'service', title: 'Choose Service', icon: Stethoscope },
  { id: 'datetime', title: 'Date & Time', icon: Calendar },
  { id: 'info', title: 'Your Details', icon: User },
  { id: 'review', title: 'Final Review', icon: Info },
];

const APPOINTMENT_TYPES = [
  { id: 'checkup', name: 'Dental Checkup', duration: '30 min', description: 'Regular examination and cleaning', icon: '🦷' },
  { id: 'emergency', name: 'Emergency Visit', duration: '60 min', description: 'Pain or urgent dental issues', icon: '🚨' },
  { id: 'whitening', name: 'Teeth Whitening', duration: '45 min', description: 'Professional whitening treatment', icon: '✨' },
  { id: 'consult', name: 'Consultation', duration: '30 min', description: 'Discuss treatment plans or braces', icon: '🤝' },
];

export default function PublicBooking() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  
  // Selection State
  const [selectedType, setSelectedType] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState<Date>(startOfToday());
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    reason: '',
    isNewPatient: true
  });

  // Fetch Page Data
  const { data: page, isLoading } = useQuery({
    queryKey: ['public-booking-page', slug],
    queryFn: () => fetchPublicPage(slug!),
    enabled: !!slug
  });

  // Mock Availability fetching for the selected date
  const [availability, setAvailability] = useState<TimeSlot[]>([]);
  useEffect(() => {
    // Simulate API call for slots
    const slots = [
      { start_time: '09:00', end_time: '09:30', is_available: true },
      { start_time: '10:00', end_time: '10:30', is_available: true },
      { start_time: '11:30', end_time: '12:00', is_available: false },
      { start_time: '14:00', end_time: '14:30', is_available: true },
      { start_time: '15:30', end_time: '16:00', is_available: true },
    ];
    setAvailability(slots);
  }, [selectedDate]);

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
      window.scrollTo(0, 0);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      window.scrollTo(0, 0);
    }
  };

  const isStepComplete = () => {
    switch (currentStep) {
      case 0: return !!selectedType;
      case 1: return !!selectedSlot;
      case 2: return formData.firstName && formData.lastName && formData.email && formData.phone;
      default: return true;
    }
  };

  if (isLoading) return <div className="h-screen flex items-center justify-center"><PageLoader /></div>;
  if (!page) return <div className="h-screen flex items-center justify-center text-red-500">Practice not found</div>;

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 overflow-x-hidden pb-20">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-20 overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-400 blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-300 blur-[120px] animate-pulse" />
      </div>

      {/* Header Section */}
      <header className="relative z-10 w-full pt-12 pb-8 px-4 text-center">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center gap-4"
        >
          {page.logo_url && (
            <div className="w-20 h-20 rounded-2xl overflow-hidden shadow-2xl border-4 border-white bg-white mb-2 ring-1 ring-slate-200">
              <img src={page.logo_url} alt={page.page_title} className="w-full h-full object-cover" />
            </div>
          )}
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 bg-clip-text">
            {page.page_title}
          </h1>
          <p className="max-w-md text-slate-500 text-lg leading-relaxed">
            {page.welcome_message}
          </p>
        </motion.div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 container max-w-4xl mx-auto px-4 mt-4">
        {/* Step Indicator */}
        <div className="mb-10 px-2 lg:px-0">
          <div className="flex justify-between items-center mb-4">
            <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Step {currentStep + 1} of {STEPS.length}</span>
            <span className="text-sm font-bold text-blue-600">{Math.round(((currentStep + 1) / STEPS.length) * 100)}% Complete</span>
          </div>
          <Progress value={((currentStep + 1) / STEPS.length) * 100} className="h-2 rounded-full bg-slate-200" />
          <div className="hidden md:flex justify-between mt-6 px-1">
            {STEPS.map((step, idx) => (
              <div key={step.id} className={cn(
                "flex items-center gap-2 group transition-all duration-300",
                currentStep >= idx ? "text-blue-600" : "text-slate-400 opacity-60"
              )}>
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                  currentStep === idx ? "bg-blue-600 text-white border-blue-600 scale-110 shadow-lg shadow-blue-100" : 
                  currentStep > idx ? "bg-blue-100 border-blue-100 text-blue-600" : "bg-transparent border-slate-300"
                )}>
                  {currentStep > idx ? <CheckCircle2 className="w-5 h-5" /> : <step.icon className="w-4 h-4" />}
                </div>
                <span className={cn("text-sm font-bold tracking-tight", currentStep === idx && "text-slate-900")}>{step.title}</span>
                {idx < STEPS.length - 1 && <div className="w-8 lg:w-16 h-[2px] bg-slate-200" />}
              </div>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            <Card className="border-none shadow-[0_20px_50px_rgba(0,0,0,0.05)] bg-white/80 backdrop-blur-xl overflow-hidden rounded-3xl ring-1 ring-slate-200/50">
              <CardContent className="p-8 md:p-12">
                
                {/* Step 1: Services */}
                {currentStep === 0 && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="space-y-2">
                      <h2 className="text-2xl font-black text-slate-800 tracking-tight">What brings you in today?</h2>
                      <p className="text-slate-500">Select the type of appointment you would like to book.</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {APPOINTMENT_TYPES.map((type) => (
                        <button
                          key={type.id}
                          onClick={() => {
                            setSelectedType(type);
                            handleNext();
                          }}
                          className={cn(
                            "group p-6 rounded-2xl text-left border-2 transition-all duration-300 hover:shadow-2xl hover:scale-[1.02]",
                            selectedType?.id === type.id 
                              ? "bg-blue-600 border-blue-600 text-white shadow-xl shadow-blue-200" 
                              : "bg-white border-slate-100 hover:border-blue-200 text-slate-800"
                          )}
                        >
                          <div className="flex justify-between items-start mb-4">
                            <span className="text-4xl">{type.icon}</span>
                            <Badge variant="outline" className={cn(
                              "font-bold uppercase tracking-widest",
                              selectedType?.id === type.id ? "border-blue-400 text-white" : "border-slate-200 text-slate-400"
                            )}>
                              {type.duration}
                            </Badge>
                          </div>
                          <h3 className="text-xl font-extrabold mb-1">{type.name}</h3>
                          <p className={cn(
                            "text-sm leading-relaxed",
                            selectedType?.id === type.id ? "text-blue-50" : "text-slate-500"
                          )}>
                            {type.description}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step 2: Date & Time */}
                {currentStep === 1 && (
                  <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="space-y-2">
                      <h2 className="text-2xl font-black text-slate-800 tracking-tight">Pick a convenient time</h2>
                      <p className="text-slate-500">We recommended booking at least 48 hours in advance.</p>
                    </div>

                    <div className="flex flex-col lg:flex-row gap-10">
                      {/* Calendar Sidebar */}
                      <div className="flex-1 space-y-6">
                        <Label className="text-sm font-bold uppercase tracking-wider text-slate-400 pl-1">Available Dates</Label>
                        <div className="grid grid-cols-7 gap-2">
                          {[...Array(14)].map((_, i) => {
                            const date = addDays(startOfToday(), i);
                            const isSelected = isSameDay(date, selectedDate);
                            return (
                              <button
                                key={i}
                                onClick={() => setSelectedDate(date)}
                                className={cn(
                                  "flex flex-col items-center justify-center p-3 rounded-2xl border-2 transition-all duration-300",
                                  isSelected 
                                    ? "bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-100 scale-105" 
                                    : "bg-slate-50 border-transparent hover:border-blue-200"
                                )}
                              >
                                <span className={cn("text-[10px] font-black uppercase mb-1", isSelected ? "text-blue-100" : "text-slate-400")}>
                                  {format(date, 'eee')}
                                </span>
                                <span className="text-lg font-black tracking-tighter">
                                  {format(date, 'd')}
                                </span>
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      {/* Time Slots */}
                      <div className="lg:w-[300px] space-y-6">
                        <Label className="text-sm font-bold uppercase tracking-wider text-slate-400 pl-1">Preferred Time</Label>
                        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                          {availability.map((slot, idx) => (
                            <button
                              key={idx}
                              disabled={!slot.is_available}
                              onClick={() => {
                                setSelectedSlot(slot.start_time);
                              }}
                              className={cn(
                                "w-full p-4 rounded-2xl flex justify-between items-center transition-all duration-300 border-2",
                                selectedSlot === slot.start_time 
                                  ? "bg-emerald-500 border-emerald-500 text-white shadow-lg shadow-emerald-100" 
                                  : slot.is_available 
                                    ? "bg-white border-slate-100 hover:border-emerald-200" 
                                    : "bg-slate-50 border-slate-50 opacity-40 cursor-not-allowed"
                              )}
                            >
                              <div className="flex items-center gap-3">
                                <Clock className={cn("w-4 h-4", selectedSlot === slot.start_time ? "text-emerald-100" : "text-slate-400")} />
                                <span className="text-lg font-black tracking-tight">{slot.start_time}</span>
                              </div>
                              {selectedSlot === slot.start_time && <CheckCircle2 className="w-5 h-5 text-white" />}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Info */}
                {currentStep === 2 && (
                  <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="space-y-2">
                      <h2 className="text-2xl font-black text-slate-800 tracking-tight">Tell us about yourself</h2>
                      <p className="text-slate-500">Please provide your contact information to finish the booking.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      <div className="space-y-6">
                        <div className="space-y-3">
                          <Label htmlFor="firstName" className="text-sm font-bold tracking-tight">First Name</Label>
                          <div className="relative group">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                            <Input 
                              id="firstName"
                              placeholder="e.g. John" 
                              className="pl-11 h-14 rounded-2xl border-slate-200 focus:ring-4 focus:ring-blue-100 transition-all font-medium"
                              value={formData.firstName}
                              onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                            />
                          </div>
                        </div>
                        <div className="space-y-3">
                          <Label htmlFor="lastName" className="text-sm font-bold tracking-tight">Last Name</Label>
                          <div className="relative group">
                             <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                            <Input 
                              id="lastName"
                              placeholder="e.g. Doe" 
                              className="pl-11 h-14 rounded-2xl border-slate-200 focus:ring-4 focus:ring-blue-100 transition-all font-medium"
                              value={formData.lastName}
                              onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-6">
                        <div className="space-y-3">
                          <Label htmlFor="email" className="text-sm font-bold tracking-tight">Email Address</Label>
                          <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                            <Input 
                              id="email"
                              type="email" 
                              placeholder="john@example.com" 
                              className="pl-11 h-14 rounded-2xl border-slate-200 focus:ring-4 focus:ring-blue-100 transition-all font-medium"
                              value={formData.email}
                              onChange={(e) => setFormData({...formData, email: e.target.value})}
                            />
                          </div>
                        </div>
                        <div className="space-y-3">
                          <Label htmlFor="phone" className="text-sm font-bold tracking-tight">Phone Number</Label>
                          <div className="relative group">
                            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                            <Input 
                              id="phone"
                              type="tel" 
                              placeholder="(555) 000-0000" 
                              className="pl-11 h-14 rounded-2xl border-slate-200 focus:ring-4 focus:ring-blue-100 transition-all font-medium"
                              value={formData.phone}
                              onChange={(e) => setFormData({...formData, phone: e.target.value})}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <Label htmlFor="reason" className="text-sm font-bold tracking-tight">Reason for visit (Optional)</Label>
                      <Textarea 
                        id="reason"
                        placeholder="Describe any symptoms or specific concerns..." 
                        className="min-h-[120px] rounded-2xl border-slate-200 focus:ring-4 focus:ring-blue-100 transition-all font-medium p-6"
                        value={formData.reason}
                        onChange={(e) => setFormData({...formData, reason: e.target.value})}
                      />
                    </div>
                  </div>
                )}

                {/* Step 4: Review */}
                {currentStep === 3 && (
                  <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="text-center space-y-2">
                       <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 text-emerald-600 mb-4 shadow-inner ring-4 ring-emerald-50">
                        <CheckCircle2 className="w-10 h-10" />
                      </div>
                      <h2 className="text-3xl font-black text-slate-800 tracking-tight">Almost there!</h2>
                      <p className="text-slate-500 text-lg">Please check the details of your appointment below.</p>
                    </div>

                    <div className="bg-slate-50 rounded-3xl p-8 border-2 border-slate-100 shadow-inner grid grid-cols-1 md:grid-cols-2 gap-10">
                      <div className="space-y-6">
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Patient Name</span>
                          <p className="text-xl font-bold flex items-center gap-2">
                            {formData.firstName} {formData.lastName}
                            <Badge variant="secondary" className="bg-blue-50 text-blue-600 border-none font-bold">New Patient</Badge>
                          </p>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Contact Information</span>
                          <div className="space-y-1">
                            <p className="text-lg font-bold flex items-center gap-2 text-slate-600">
                              <Mail className="w-4 h-4" /> {formData.email}
                            </p>
                            <p className="text-lg font-bold flex items-center gap-2 text-slate-600">
                              <Phone className="w-4 h-4" /> {formData.phone}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-6">
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Appointment Type</span>
                          <p className="text-xl font-bold text-blue-600">{selectedType?.name}</p>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Date & Time</span>
                          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 mt-2">
                            <p className="text-lg font-black text-slate-800 flex items-center gap-2">
                              <Calendar className="w-5 h-5 text-blue-500" />
                              {format(selectedDate, 'EEEE, MMMM d, yyyy')}
                            </p>
                            <p className="text-2xl font-black text-emerald-600 flex items-center gap-2 mt-1">
                              <Clock className="w-6 h-6 text-emerald-500" />
                              {selectedSlot}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-amber-50 rounded-2xl p-6 border border-amber-200/50 flex gap-4">
                      <AlertCircle className="w-6 h-6 text-amber-500 shrink-0 mt-1" />
                      <p className="text-sm text-amber-800 leading-relaxed font-medium">
                        <strong>Important:</strong> Your booking is a "Request" until confirmed by our staff. 
                        You will receive an email confirmation once we review your appointment.
                      </p>
                    </div>
                  </div>
                )}

              </CardContent>

              {/* Action Bar */}
              <div className="bg-slate-50/50 border-t border-slate-100 p-6 flex items-center justify-between gap-4">
                <Button 
                  variant="ghost" 
                  onClick={handleBack}
                  disabled={currentStep === 0}
                  className="px-8 h-12 rounded-xl border-none font-bold text-slate-500 hover:text-slate-900 transition-all hover:bg-slate-100"
                >
                  <ChevronLeft className="w-5 h-5 mr-1" /> Back
                </Button>
                
                {currentStep === STEPS.length - 1 ? (
                  <Button 
                    onClick={() => {
                      toast({
                        title: "Booking Submitted!",
                        description: "Your request has been sent to the clinic.",
                      });
                      navigate('/book/success');
                    }}
                    className="px-12 h-14 rounded-2xl font-black text-lg bg-emerald-600 hover:bg-emerald-700 shadow-xl shadow-emerald-100 transition-all hover:scale-[1.05] active:scale-95 text-white"
                  >
                    Confirm Booking <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                ) : (
                  <Button 
                    disabled={!isStepComplete()}
                    onClick={handleNext}
                    className="px-12 h-14 rounded-2xl font-black text-lg bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all hover:scale-[1.05] active:scale-95 text-white"
                  >
                    Continue <ChevronRight className="ml-2 w-5 h-5" />
                  </Button>
                )}
              </div>
            </Card>
          </motion.div>
        </AnimatePresence>

        {/* Footer Info */}
        <div className="mt-12 text-center text-slate-400 space-y-4">
          <div className="flex items-center justify-center gap-6">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              <span className="text-xs font-bold uppercase tracking-widest">123 Dental Lane, New York, NY</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4" />
              <span className="text-xs font-bold uppercase tracking-widest">(555) 123-4567</span>
            </div>
          </div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] opacity-40">Powered by CoreDent Prime • Enterprise Clinical Systems</p>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #e2e8f0;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #cbd5e1;
        }
      `}} />
    </div>
  );
}
