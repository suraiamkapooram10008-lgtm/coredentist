// ============================================
// CoreDent PMS - Application Shell
// Main layout with sidebar navigation
// ============================================

import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/auth-context';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { FeatureBoundary } from '../FeatureBoundary';
import { cn } from '@/lib/utils';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();

  // Determine feature name from path (e.g., /patients -> Patients)
  const rawPath = location.pathname.split('/')[1] || 'Dashboard';
  const featureName = (rawPath?.charAt(0) || '?').toUpperCase() + (rawPath?.slice(1) || '');

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar 
        collapsed={sidebarCollapsed} 
        mobileOpen={mobileOpen}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
        onMobileClose={() => setMobileOpen(false)}
      />
      
      {/* Main content area */}
      <div 
        className={cn(
          "transition-all duration-300",
          sidebarCollapsed ? "lg:ml-16" : "lg:ml-64"
        )}
      >
        {/* Header */}
        <Header 
          user={user} 
          onMenuToggle={() => setMobileOpen(!mobileOpen)}
        />
        
        {/* Page content with enter animation and feature protection */}
        <main className="p-4 lg:p-6 page-enter">
          <FeatureBoundary featureName={featureName} key={location.pathname}>
            {children}
          </FeatureBoundary>
        </main>
      </div>
    </div>
  );
}
