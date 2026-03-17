/**
 * Insurance Page Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/test-utils';
import Insurance from '@/pages/Insurance';

// Mock the lucide-react icons
vi.mock('lucide-react', () => ({
  Search: () => <span data-testid="search-icon" />,
  Plus: () => <span data-testid="plus-icon" />,
  Shield: () => <span data-testid="shield-icon" />,
  Clock: () => <span data-testid="clock-icon" />,
  CheckCircle: () => <span data-testid="check-icon" />,
  AlertCircle: () => <span data-testid="alert-icon" />,
  DollarSign: () => <span data-testid="dollar-icon" />,
  FileText: () => <span data-testid="file-icon" />,
  Upload: () => <span data-testid="upload-icon" />,
  Download: () => <span data-testid="download-icon" />,
  Eye: () => <span data-testid="eye-icon" />,
}));

// Mock the insurance API
vi.mock('@/services/insuranceApi', () => ({
  insuranceApi: {
    getClaims: vi.fn().mockResolvedValue([]),
    getCarriers: vi.fn().mockResolvedValue([]),
    getSummary: vi.fn().mockResolvedValue({
      totalClaims: 0,
      pending: 0,
      approved: 0,
      denied: 0,
      totalPaid: 0,
    }),
  },
}));

const mockUser = {
  id: '1',
  email: 'admin@test.com',
  firstName: 'Admin',
  lastName: 'User',
  role: 'admin' as const,
  practiceId: '1',
  practiceName: 'Test Practice',
};

describe('Insurance Page', () => {
  it('renders insurance page title', () => {
    renderWithProviders(<Insurance />, {
      user: mockUser,
      isAuthenticated: true,
    });
    
    expect(screen.getByText('Insurance Management')).toBeInTheDocument();
  });

  it('renders summary cards', () => {
    renderWithProviders(<Insurance />, {
      user: mockUser,
      isAuthenticated: true,
    });
    
    expect(screen.getByText('Active Claims')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('Approved')).toBeInTheDocument();
    expect(screen.getByText('Total Paid')).toBeInTheDocument();
  });

  it('renders tabs for different sections', () => {
    renderWithProviders(<Insurance />, {
      user: mockUser,
      isAuthenticated: true,
    });
    
    expect(screen.getByText('Claims')).toBeInTheDocument();
    expect(screen.getByText('Eligibility')).toBeInTheDocument();
    expect(screen.getByText('EOBs')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('has New Claim button', () => {
    renderWithProviders(<Insurance />, {
      user: mockUser,
      isAuthenticated: true,
    });
    
    expect(screen.getByText('New Claim')).toBeInTheDocument();
  });
});
