import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CookieConsent } from "@/components/CookieConsent";
import { PageLoader } from "@/components/ui/spinner";
import { Suspense, lazy, useEffect } from "react";

// Lazy load pages for performance
const Login = lazy(() => import("./pages/Login"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const AcceptInvitation = lazy(() => import("./pages/AcceptInvitation"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Schedule = lazy(() => import("./pages/Schedule"));
const PatientList = lazy(() => import("./pages/patients/PatientList"));
const PatientProfile = lazy(() => import("./pages/patients/PatientProfile"));
const DentalChart = lazy(() => import("./pages/DentalChart"));
const TreatmentPlans = lazy(() => import("./pages/TreatmentPlans"));
const Billing = lazy(() => import("./pages/Billing"));
const Reports = lazy(() => import("./pages/Reports"));
const Settings = lazy(() => import("./pages/Settings"));
const NotFound = lazy(() => import("./pages/NotFound"));
const ClinicalNotes = lazy(() => import("./pages/ClinicalNotes"));
// New module pages
const Insurance = lazy(() => import("./pages/Insurance"));
const Imaging = lazy(() => import("./pages/Imaging"));
const Appointments = lazy(() => import("./pages/Appointments"));
const OnlineBooking = lazy(() => import("./pages/OnlineBooking"));
const Inventory = lazy(() => import("./pages/Inventory"));
const LabManagement = lazy(() => import("./pages/LabManagement"));
const Referrals = lazy(() => import("./pages/Referrals"));
const Communications = lazy(() => import("./pages/Communications"));
const Marketing = lazy(() => import("./pages/Marketing"));
const Documents = lazy(() => import("./pages/Documents"));
const Payments = lazy(() => import("./pages/Payments"));
const PublicBooking = lazy(() => import("./pages/PublicBooking"));
const BookingSuccess = lazy(() => import("./pages/BookingSuccess"));
const RevenueLanding = lazy(() => import("./pages/RevenueLanding"));
const BillingPortal = lazy(() => import("./pages/BillingPortal"));
const ImagingHub = lazy(() => import("./pages/ImagingHub"));
const EnterpriseHQ = lazy(() => import("./pages/EnterpriseHQ"));
const ReferralHub = lazy(() => import("./pages/ReferralHub"));
const LabLogistics = lazy(() => import("./pages/LabLogistics"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 minutes before data is considered stale
      gcTime: 10 * 60 * 1000,       // 10 minutes garbage collection
      retry: 2,                      // Retry failed requests twice
      refetchOnWindowFocus: false,   // Don't refetch on tab focus (medical data shouldn't change under you)
    },
    mutations: {
      retry: 1,
    },
  },
});

const App = () => {
  // Register service worker for offline mode
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((registration) => {
            console.log("SW registered:", registration.scope);
          })
          .catch((error) => {
            console.log("SW registration failed:", error);
          });
      });
    }
  }, []);

  return (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <Toaster />
          <Sonner />
          <CookieConsent />
          <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Public routes - Auth flows */}
                <Route path="/login" element={<Login />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
                <Route path="/accept-invitation" element={<AcceptInvitation />} />
                
                {/* Public Booking Portal */}
                <Route path="/book/success" element={<BookingSuccess />} />
                <Route path="/book/:slug" element={<PublicBooking />} />
                
                {/* Protected routes with AppShell */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <AppShell>
                        <Dashboard />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                
                {/* Patient Management routes */}
                <Route
                  path="/patients"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist', 'front_desk']}>
                      <AppShell>
                        <PatientList />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/patients/:id"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist', 'front_desk']}>
                      <AppShell>
                        <PatientProfile />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/schedule/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist', 'front_desk']}>
                      <AppShell>
                        <Schedule />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Dental Chart - Dentist only */}
                <Route
                  path="/chart"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'dentist']}>
                      <AppShell>
                        <DentalChart />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/chart/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'dentist']}>
                      <AppShell>
                        <DentalChart />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Treatment Plans - Dentist access */}
                <Route
                  path="/treatment-plans"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'dentist']}>
                      <AppShell>
                        <TreatmentPlans />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/treatment-plans/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'dentist']}>
                      <AppShell>
                        <TreatmentPlans />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notes"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist']}>
                      <AppShell>
                        <ClinicalNotes />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notes/:id"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist']}>
                      <AppShell>
                        <ClinicalNotes />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notes/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist']}>
                      <AppShell>
                        <ClinicalNotes />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Billing - Admin and Front Desk access */}
                <Route
                  path="/billing"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Billing />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/billing/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Billing />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Reports - Owner and Admin only */}
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <Reports />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <Reports />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Settings - Owner and Admin only */}
                <Route
                  path="/settings"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <Settings />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/settings/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <Settings />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Revenue - Admin access */}
                <Route
                  path="/revenue"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <RevenueLanding />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Billing Portal - Admin access */}
                <Route
                  path="/billing-portal"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <BillingPortal />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Imaging Hub - Dentist and Hygienist */}
                <Route
                  path="/imaging-hub"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist', 'hygienist']}>
                      <AppShell>
                        <ImagingHub />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Enterprise HQ - Owner and Admin */}
                <Route
                  path="/enterprise/hq"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <EnterpriseHQ />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Referral Hub - Multiple roles */}
                <Route
                  path="/referrals/hub"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist', 'hygienist', 'front_desk']}>
                      <AppShell>
                        <ReferralHub />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Lab Logistics - Multiple roles */}
                <Route
                  path="/lab/logistics"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist', 'hygienist', 'front_desk']}>
                      <AppShell>
                        <LabLogistics />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Insurance Management */}
                <Route
                  path="/insurance"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Insurance />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/insurance/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Insurance />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Imaging Management - Admin and Dentist */}
                <Route
                  path="/imaging"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist']}>
                      <AppShell>
                        <Imaging />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/imaging/*"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist']}>
                      <AppShell>
                        <Imaging />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Appointments */}
                <Route
                  path="/appointments"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Appointments />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Online Booking */}
                <Route
                  path="/online-booking"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <OnlineBooking />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Inventory */}
                <Route
                  path="/inventory"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <Inventory />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Lab Management */}
                <Route
                  path="/labs"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'dentist']}>
                      <AppShell>
                        <LabManagement />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Referrals */}
                <Route
                  path="/referrals"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Referrals />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Communications */}
                <Route
                  path="/communications"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Communications />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Marketing */}
                <Route
                  path="/marketing"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin']}>
                      <AppShell>
                        <Marketing />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Documents */}
                <Route
                  path="/documents"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Documents />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                {/* Payments */}
                <Route
                  path="/payments"
                  element={
                    <ProtectedRoute allowedRoles={['owner', 'admin', 'front_desk']}>
                      <AppShell>
                        <Payments />
                      </AppShell>
                    </ProtectedRoute>
                  }
                />
                
                {/* Redirect root to dashboard */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                
                {/* 404 */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </ErrorBoundary>
  );
};

export default App;