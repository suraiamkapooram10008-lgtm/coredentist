/**
 * Route Configuration
 * Centralized route definitions for better maintainability
 */

import React from 'react';
import type { UserRole } from '@/types/api';

export interface RouteConfig {
  path: string;
  component: React.LazyExoticComponent<() => JSX.Element>;
  roles?: UserRole[];
  title?: string;
  // For routes with dynamic segments like /patients/:id
  children?: Omit<RouteConfig, 'path'>[];
}

// Lazy load all page components
const Login = React.lazy(() => import('@/pages/Login'));
const ForgotPassword = React.lazy(() => import('@/pages/ForgotPassword'));
const ResetPassword = React.lazy(() => import('@/pages/ResetPassword'));
const AcceptInvitation = React.lazy(() => import('@/pages/AcceptInvitation'));
const Dashboard = React.lazy(() => import('@/pages/Dashboard'));
const Schedule = React.lazy(() => import('@/pages/Schedule'));
const PatientList = React.lazy(() => import('@/pages/patients/PatientList'));
const PatientProfile = React.lazy(() => import('@/pages/patients/PatientProfile'));
const DentalChart = React.lazy(() => import('@/pages/DentalChart'));
const TreatmentPlans = React.lazy(() => import('@/pages/TreatmentPlans'));
const Billing = React.lazy(() => import('@/pages/Billing'));
const Reports = React.lazy(() => import('@/pages/Reports'));
const Settings = React.lazy(() => import('@/pages/Settings'));
const ClinicalNotes = React.lazy(() => import('@/pages/ClinicalNotes'));
const Insurance = React.lazy(() => import('@/pages/Insurance'));
const Imaging = React.lazy(() => import('@/pages/Imaging'));
const Appointments = React.lazy(() => import('@/pages/Appointments'));
const OnlineBooking = React.lazy(() => import('@/pages/OnlineBooking'));
const Inventory = React.lazy(() => import('@/pages/Inventory'));
const LabManagement = React.lazy(() => import('@/pages/LabManagement'));
const Referrals = React.lazy(() => import('@/pages/Referrals'));
const Communications = React.lazy(() => import('@/pages/Communications'));
const Marketing = React.lazy(() => import('@/pages/Marketing'));
const Documents = React.lazy(() => import('@/pages/Documents'));
const Payments = React.lazy(() => import('@/pages/Payments'));
const PublicBooking = React.lazy(() => import('@/pages/PublicBooking'));
const BookingSuccess = React.lazy(() => import('@/pages/BookingSuccess'));
const RevenueLanding = React.lazy(() => import('@/pages/RevenueLanding'));
const BillingPortal = React.lazy(() => import('@/pages/BillingPortal'));
const ImagingHub = React.lazy(() => import('@/pages/ImagingHub'));
const EnterpriseHQ = React.lazy(() => import('@/pages/EnterpriseHQ'));
const ReferralHub = React.lazy(() => import('@/pages/ReferralHub'));
const LabLogistics = React.lazy(() => import('@/pages/LabLogistics'));
const Subscriptions = React.lazy(() => import('@/pages/Subscriptions'));
const NotFound = React.lazy(() => import('@/pages/NotFound'));

/**
 * Public routes (no authentication required)
 */
export const publicRoutes: RouteConfig[] = [
  { path: '/login', component: Login },
  { path: '/forgot-password', component: ForgotPassword },
  { path: '/reset-password', component: ResetPassword },
  { path: '/accept-invitation', component: AcceptInvitation },
  // Public booking portal
  { path: '/book/success', component: BookingSuccess },
  { path: '/book/:slug', component: PublicBooking },
];

/**
 * Protected routes grouped by feature area
 * Each group can have its own role-based access control
 */
export const protectedRoutes: RouteConfig[] = [
  // Dashboard
  { 
    path: '/dashboard', 
    component: Dashboard,
    title: 'Dashboard',
  },

  // Patient Management
  { 
    path: '/patients', 
    component: PatientList,
    roles: ['owner', 'admin', 'dentist', 'front_desk'],
    title: 'Patients',
  },
  { 
    path: '/patients/:id', 
    component: PatientProfile,
    roles: ['owner', 'admin', 'dentist', 'front_desk'],
    title: 'Patient Profile',
  },

  // Scheduling
  { 
    path: '/schedule/*', 
    component: Schedule,
    roles: ['owner', 'admin', 'dentist', 'front_desk'],
    title: 'Schedule',
  },

  // Clinical - Dentist only
  { 
    path: '/chart', 
    component: DentalChart,
    roles: ['owner', 'dentist'],
    title: 'Dental Chart',
  },
  { 
    path: '/chart/*', 
    component: DentalChart,
    roles: ['owner', 'dentist'],
    title: 'Dental Chart',
  },

  // Treatment Plans
  { 
    path: '/treatment-plans', 
    component: TreatmentPlans,
    roles: ['owner', 'dentist'],
    title: 'Treatment Plans',
  },
  { 
    path: '/treatment-plans/*', 
    component: TreatmentPlans,
    roles: ['owner', 'dentist'],
    title: 'Treatment Plans',
  },

  // Clinical Notes
  { 
    path: '/notes', 
    component: ClinicalNotes,
    roles: ['owner', 'admin', 'dentist'],
    title: 'Clinical Notes',
  },
  { 
    path: '/notes/:id', 
    component: ClinicalNotes,
    roles: ['owner', 'admin', 'dentist'],
    title: 'Clinical Notes',
  },
  { 
    path: '/notes/*', 
    component: ClinicalNotes,
    roles: ['owner', 'admin', 'dentist'],
    title: 'Clinical Notes',
  },

  // Billing
  { 
    path: '/billing', 
    component: Billing,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Billing',
  },
  { 
    path: '/billing/*', 
    component: Billing,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Billing',
  },

  // Reports - Owner and Admin only
  { 
    path: '/reports', 
    component: Reports,
    roles: ['owner', 'admin'],
    title: 'Reports',
  },
  { 
    path: '/reports/*', 
    component: Reports,
    roles: ['owner', 'admin'],
    title: 'Reports',
  },

  // Settings
  { 
    path: '/settings', 
    component: Settings,
    roles: ['owner', 'admin'],
    title: 'Settings',
  },
  { 
    path: '/settings/*', 
    component: Settings,
    roles: ['owner', 'admin'],
    title: 'Settings',
  },

  // Revenue Management
  { 
    path: '/revenue', 
    component: RevenueLanding,
    roles: ['owner', 'admin'],
    title: 'Revenue',
  },

  // Billing Portal
  { 
    path: '/billing-portal', 
    component: BillingPortal,
    roles: ['owner', 'admin'],
    title: 'Billing Portal',
  },

  // Imaging Hub
  { 
    path: '/imaging-hub', 
    component: ImagingHub,
    roles: ['owner', 'admin', 'dentist', 'hygienist'],
    title: 'Imaging Hub',
  },

  // Enterprise HQ
  { 
    path: '/enterprise/hq', 
    component: EnterpriseHQ,
    roles: ['owner', 'admin'],
    title: 'Enterprise HQ',
  },

  // Referral Hub
  { 
    path: '/referrals/hub', 
    component: ReferralHub,
    roles: ['owner', 'admin', 'dentist', 'hygienist', 'front_desk'],
    title: 'Referral Hub',
  },

  // Lab Logistics
  { 
    path: '/lab/logistics', 
    component: LabLogistics,
    roles: ['owner', 'admin', 'dentist', 'hygienist', 'front_desk'],
    title: 'Lab Logistics',
  },

  // Insurance Management
  { 
    path: '/insurance', 
    component: Insurance,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Insurance',
  },
  { 
    path: '/insurance/*', 
    component: Insurance,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Insurance',
  },

  // Imaging Management
  { 
    path: '/imaging', 
    component: Imaging,
    roles: ['owner', 'admin', 'dentist'],
    title: 'Imaging',
  },
  { 
    path: '/imaging/*', 
    component: Imaging,
    roles: ['owner', 'admin', 'dentist'],
    title: 'Imaging',
  },

  // Appointments
  { 
    path: '/appointments', 
    component: Appointments,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Appointments',
  },

  // Online Booking
  { 
    path: '/online-booking', 
    component: OnlineBooking,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Online Booking',
  },

  // Inventory
  { 
    path: '/inventory', 
    component: Inventory,
    roles: ['owner', 'admin'],
    title: 'Inventory',
  },

  // Lab Management
  { 
    path: '/labs', 
    component: LabManagement,
    roles: ['owner', 'admin', 'dentist'],
    title: 'Lab Management',
  },

  // Referrals
  { 
    path: '/referrals', 
    component: Referrals,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Referrals',
  },

  // Communications
  { 
    path: '/communications', 
    component: Communications,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Communications',
  },

  // Marketing
  { 
    path: '/marketing', 
    component: Marketing,
    roles: ['owner', 'admin'],
    title: 'Marketing',
  },

  // Documents
  { 
    path: '/documents', 
    component: Documents,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Documents',
  },

  // Payments
  { 
    path: '/payments', 
    component: Payments,
    roles: ['owner', 'admin', 'front_desk'],
    title: 'Payments',
  },

  // Subscriptions
  { 
    path: '/subscriptions', 
    component: Subscriptions,
    roles: ['owner', 'admin'],
    title: 'Subscriptions',
  },
];

/**
 * 404 route
 */
export const notFoundRoute: RouteConfig = {
  path: '*',
  component: NotFound,
};

/**
 * Default redirect after login
 */
export const DEFAULT_LOGIN_REDIRECT = '/dashboard';