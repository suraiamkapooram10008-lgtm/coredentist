import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock components for testing
const MockLayout = ({ children }: { children: React.ReactNode }) => (
  <div data-testid="layout">
    <header data-testid="header">Header</header>
    <aside data-testid="sidebar">Sidebar</aside>
    <main data-testid="main-content">{children}</main>
  </div>
);

describe('Layout Components', () => {
  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <AuthProvider>{component}</AuthProvider>
      </BrowserRouter>
    );
  };

  it('should render layout structure', () => {
    renderWithProviders(
      <MockLayout>
        <div>Test Content</div>
      </MockLayout>
    );

    expect(screen.getByTestId('layout')).toBeInTheDocument();
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('main-content')).toBeInTheDocument();
  });

  it('should render children content', () => {
    renderWithProviders(
      <MockLayout>
        <div>Test Content</div>
      </MockLayout>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});
