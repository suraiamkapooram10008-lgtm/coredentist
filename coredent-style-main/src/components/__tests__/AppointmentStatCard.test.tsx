/**
 * AppointmentStatCard Component Tests
 */

import { render, screen } from '@testing-library/react';
import { AppointmentStatCard } from '../appointments/AppointmentStatCard';
import { Calendar } from 'lucide-react';

describe('AppointmentStatCard', () => {
  it('should render stat card with title and value', () => {
    render(
      <AppointmentStatCard
        title="Today's Appointments"
        value={5}
        icon={Calendar}
        color="text-blue-500"
      />
    );

    expect(screen.getByText("Today's Appointments")).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('should display loading skeleton when isLoading is true', () => {
    const { container } = render(
      <AppointmentStatCard
        title="Today's Appointments"
        value={5}
        icon={Calendar}
        color="text-blue-500"
        isLoading={true}
      />
    );

    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  it('should apply correct color class', () => {
    const { container } = render(
      <AppointmentStatCard
        title="Confirmed"
        value={10}
        icon={Calendar}
        color="text-green-500"
      />
    );

    const valueElement = container.querySelector('.text-green-500');
    expect(valueElement).toBeInTheDocument();
  });

  it('should render icon', () => {
    const { container } = render(
      <AppointmentStatCard
        title="Today's Appointments"
        value={5}
        icon={Calendar}
        color="text-blue-500"
      />
    );

    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should handle zero value', () => {
    render(
      <AppointmentStatCard
        title="Cancelled"
        value={0}
        icon={Calendar}
        color="text-red-500"
      />
    );

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('should handle large values', () => {
    render(
      <AppointmentStatCard
        title="Total Appointments"
        value={9999}
        icon={Calendar}
        color="text-blue-500"
      />
    );

    expect(screen.getByText('9999')).toBeInTheDocument();
  });

  it('should display lowercase title in description', () => {
    render(
      <AppointmentStatCard
        title="Today's Appointments"
        value={5}
        icon={Calendar}
        color="text-blue-500"
      />
    );

    expect(screen.getByText("today's appointments")).toBeInTheDocument();
  });

  it('should be memoized', () => {
    const { rerender } = render(
      <AppointmentStatCard
        title="Today's Appointments"
        value={5}
        icon={Calendar}
        color="text-blue-500"
      />
    );

    const firstRender = screen.getByText('5');

    rerender(
      <AppointmentStatCard
        title="Today's Appointments"
        value={5}
        icon={Calendar}
        color="text-blue-500"
      />
    );

    const secondRender = screen.getByText('5');
    expect(firstRender).toBe(secondRender);
  });
});
