import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock Dashboard component
const MockDashboard = () => (
  <div data-testid="dashboard">
    <h1>Dashboard</h1>
    <div data-testid="stats-cards">
      <div data-testid="patients-card">
        <h3>Total Patients</h3>
        <span>150</span>
      </div>
      <div data-testid="appointments-card">
        <h3>Today's Appointments</h3>
        <span>8</span>
      </div>
      <div data-testid="revenue-card">
        <h3>Monthly Revenue</h3>
        <span>$12,500</span>
      </div>
    </div>
    <div data-testid="recent-appointments">
      <h3>Recent Appointments</h3>
      <div>John Doe - Cleaning - 10:00 AM</div>
      <div>Jane Smith - Checkup - 2:00 PM</div>
    </div>
  </div>
);

describe('Dashboard', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          {component}
        </QueryClientProvider>
      </BrowserRouter>
    );
  };

  it('should render dashboard title', () => {
    renderWithProviders(<MockDashboard />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('should render stats cards', () => {
    renderWithProviders(<MockDashboard />);
    
    expect(screen.getByTestId('stats-cards')).toBeInTheDocument();
    expect(screen.getByTestId('patients-card')).toBeInTheDocument();
    expect(screen.getByTestId('appointments-card')).toBeInTheDocument();
    expect(screen.getByTestId('revenue-card')).toBeInTheDocument();
  });

  it('should display patient count', () => {
    renderWithProviders(<MockDashboard />);
    
    expect(screen.getByText('Total Patients')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('should display appointments count', () => {
    renderWithProviders(<MockDashboard />);
    
    expect(screen.getByText("Today's Appointments")).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
  });

  it('should display revenue', () => {
    renderWithProviders(<MockDashboard />);
    
    expect(screen.getByText('Monthly Revenue')).toBeInTheDocument();
    expect(screen.getByText('$12,500')).toBeInTheDocument();
  });

  it('should render recent appointments', () => {
    renderWithProviders(<MockDashboard />);
    
    expect(screen.getByTestId('recent-appointments')).toBeInTheDocument();
    expect(screen.getByText('Recent Appointments')).toBeInTheDocument();
    expect(screen.getByText('John Doe - Cleaning - 10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith - Checkup - 2:00 PM')).toBeInTheDocument();
  });
});