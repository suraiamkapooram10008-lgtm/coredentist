import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  createAppointment,
  listAppointments,
} from "@/services/appointmentsApi";
import {
  useAppointments,
  useCreateAppointment,
} from "../useAppointments";

vi.mock("@/services/appointmentsApi", () => ({
  createAppointment: vi.fn(),
  deleteAppointment: vi.fn(),
  getAppointmentStats: vi.fn(),
  listAppointments: vi.fn(),
  listAppointmentTypes: vi.fn(),
  sendAppointmentReminder: vi.fn(),
  updateAppointment: vi.fn(),
}));

const mockedCreateAppointment = vi.mocked(createAppointment);
const mockedListAppointments = vi.mocked(listAppointments);

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe("useAppointments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("surfaces API failure instead of returning fabricated appointments", async () => {
    mockedListAppointments.mockResolvedValue({
      success: false,
      error: { code: "UNAVAILABLE", message: "Scheduling service unavailable" },
    });

    const { result } = renderHook(
      () => useAppointments({ date: "2026-06-21" }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toEqual(new Error("Scheduling service unavailable"));
  });

  it("creates appointments through the API and invokes the success callback", async () => {
    const appointment = {
      patient: "patient-1",
      patientName: "Jamie Rivera",
      time: "10:00 AM",
      duration: "30",
      type: "Exam",
      dentist: "Dr. Chen",
      status: "Pending" as const,
      date: "2026-06-22",
    };
    mockedCreateAppointment.mockResolvedValue({
      success: true,
      data: { id: "appointment-1", ...appointment },
    });
    const onSuccess = vi.fn();

    const { result } = renderHook(
      () => useCreateAppointment({ onSuccess }),
      { wrapper: createWrapper() },
    );

    await act(async () => {
      await result.current.mutateAsync(appointment);
    });

    expect(mockedCreateAppointment).toHaveBeenCalledWith(appointment);
    expect(onSuccess).toHaveBeenCalledOnce();
  });
});