import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { 
  ArrowRight, 
  Stethoscope, 
  BrainCircuit, 
  Building2, 
  FileSignature, 
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';

export default function Landing() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background selection:bg-primary/20 flex flex-col font-sans">
      
      {/* ── Navigation ── */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Stethoscope className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl tracking-tight">CoreDent</span>
          </div>
          <div className="hidden md:flex gap-6 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-primary transition-colors">Features</a>
            <a href="#solutions" className="hover:text-primary transition-colors">Solutions</a>
            <a href="#pricing" className="hover:text-primary transition-colors">Pricing</a>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Link to="/dashboard">
                <Button>Go to Dashboard</Button>
              </Link>
            ) : (
              <>
                <Link to="/login" className="hidden sm:inline-block">
                  <Button variant="ghost">Sign In</Button>
                </Link>
                <Link to="/register">
                  <Button>Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* ── Hero Section ── */}
        <section className="relative overflow-hidden pt-24 pb-32 lg:pt-36 lg:pb-40">
          {/* Background Gradients */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full -z-10 opacity-30 dark:opacity-20 pointer-events-none">
            <div className="absolute top-[20%] left-[10%] w-[500px] h-[500px] bg-primary/40 blur-[120px] rounded-full mix-blend-multiply" />
            <div className="absolute top-[30%] right-[10%] w-[400px] h-[400px] bg-indigo-500/40 blur-[120px] rounded-full mix-blend-multiply" />
          </div>

          <div className="container mx-auto px-4 text-center">
            <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 mb-8 animate-fade-in-up">
              <Sparkles className="h-3.5 w-3.5 mr-2 text-indigo-500" />
              Next-Gen Dental OS is Here
            </div>
            
            <h1 className="max-w-4xl mx-auto text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-foreground mb-8 bg-clip-text">
              The Intelligent Platform for <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-indigo-600">
                Modern Dental Enterprises
              </span>
            </h1>
            
            <p className="max-w-2xl mx-auto text-xl text-muted-foreground mb-10">
              Unify your clinical charting, AI imaging, and billing in one lightning-fast platform. Built for growing DSOs and forward-thinking practices.
            </p>
            
            <div className="flex flex-col sm:flex-row justify-center items-center gap-4">
              <Link to={user ? "/dashboard" : "/register"}>
                <Button size="lg" className="h-14 px-8 text-lg rounded-full shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all hover:-translate-y-0.5">
                  Start Your Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>
            
            <div className="mt-16 flex justify-center gap-8 text-sm font-medium text-muted-foreground/80">
              <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" /> No credit card required</div>
              <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" /> 14-day free trial</div>
              <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-green-500" /> Cancel anytime</div>
            </div>
          </div>
        </section>

        {/* ── Features Section ── */}
        <section id="features" className="py-24 bg-accent/30">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Everything you need to scale</h2>
              <p className="text-lg text-muted-foreground">Replace your legacy servers with a cloud-native platform designed for speed, security, and intelligence.</p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className="p-8 rounded-3xl bg-background border shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <BrainCircuit className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-bold mb-3">AI-Powered Diagnostics</h3>
                <p className="text-muted-foreground">Instantly overlay diagnostic findings on digital X-rays to improve case acceptance and clinical accuracy.</p>
              </div>

              {/* Feature 2 */}
              <div className="p-8 rounded-3xl bg-background border shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-6">
                  <Building2 className="h-6 w-6 text-indigo-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">True DSO Architecture</h3>
                <p className="text-muted-foreground">Manage multiple locations, share patient records globally, and analyze enterprise revenue from a single dashboard.</p>
              </div>

              {/* Feature 3 */}
              <div className="p-8 rounded-3xl bg-background border shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-rose-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="h-12 w-12 rounded-xl bg-rose-500/10 flex items-center justify-center mb-6">
                  <FileSignature className="h-6 w-6 text-rose-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">Digital Intake Forms</h3>
                <p className="text-muted-foreground">Send HIPAA-compliant consent forms and health histories to patients' phones before they walk in the door.</p>
              </div>
              
              {/* Feature 4 */}
              <div className="p-8 rounded-3xl bg-background border shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="h-12 w-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-6">
                  <ShieldCheck className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">Automated ERA Workflows</h3>
                <p className="text-muted-foreground">Stop manually posting payments. Automatically process 835 files and manage actionable claim denials.</p>
              </div>

              {/* Feature 5 */}
              <div className="p-8 rounded-3xl bg-background border shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="h-12 w-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-6">
                  <Zap className="h-6 w-6 text-amber-600" />
                </div>
                <h3 className="text-xl font-bold mb-3">1-Click Migration</h3>
                <p className="text-muted-foreground">Upload your legacy Dentrix or OpenDental exports and we automatically migrate your entire patient base.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── Pricing Section ── */}
        <section id="pricing" className="py-24">
          <div className="container mx-auto px-4">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Simple, transparent pricing</h2>
              <p className="text-lg text-muted-foreground">Choose the plan that fits your practice's growth.</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* Pro Plan */}
              <div className="rounded-3xl border bg-card text-card-foreground p-8 shadow-sm flex flex-col">
                <h3 className="text-2xl font-bold mb-2">Solo Practice</h3>
                <p className="text-muted-foreground mb-6">Everything you need for a single location.</p>
                <div className="mb-6 flex items-baseline text-5xl font-extrabold">
                  $349
                  <span className="text-lg font-medium text-muted-foreground ml-2">/mo</span>
                </div>
                <ul className="space-y-4 mb-8 flex-1">
                  {['Unlimited Patients', 'Digital Intake Forms', 'Native X-Ray Imaging', 'Online Booking Portal'].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-primary" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button variant="outline" className="w-full h-12 text-lg rounded-xl">Start Free Trial</Button>
              </div>

              {/* Enterprise Plan */}
              <div className="rounded-3xl border-2 border-primary bg-card text-card-foreground p-8 shadow-xl relative flex flex-col scale-[1.02]">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary text-primary-foreground px-4 py-1 rounded-full text-sm font-bold tracking-wide">
                  MOST POPULAR
                </div>
                <h3 className="text-2xl font-bold mb-2">DSO / Enterprise</h3>
                <p className="text-muted-foreground mb-6">Advanced features for multi-location groups.</p>
                <div className="mb-6 flex items-baseline text-5xl font-extrabold">
                  $599
                  <span className="text-lg font-medium text-muted-foreground ml-2">/mo per location</span>
                </div>
                <ul className="space-y-4 mb-8 flex-1">
                  {['Everything in Solo', 'Global Patient Records', 'AI Diagnostic Overlays', 'Automated ERA Posting', 'Centralized Billing Hub'].map((feature) => (
                    <li key={feature} className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-primary" />
                      <span className={feature === 'Everything in Solo' ? 'font-semibold' : ''}>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button className="w-full h-12 text-lg rounded-xl shadow-lg shadow-primary/25">Contact Sales</Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t bg-muted/40 py-12">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-6 w-6 text-primary" />
            <span className="font-bold text-lg">CoreDent</span>
          </div>
          <div className="text-sm text-muted-foreground">
            © 2026 CoreDent PMS. All rights reserved.
          </div>
          <div className="flex gap-4 text-sm font-medium">
            {/* TODO: Wire to real policy pages before launch */}
          </div>
        </div>
      </footer>
    </div>
  );
}
