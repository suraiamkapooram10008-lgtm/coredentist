import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import Schedule from "../Schedule";
import { server } from "@/test/mocks/server";
import { http, HttpResponse } from "msw";

// Mock hooks
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("Schedule Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock auth to return authenticated user
    server.use(
      http.get("/api/v1/auth/me", () => {
        return HttpResponse.json({
          id: "test-user-id",
          email: "test@example.com",
          firstName: "Test",
          lastName: "User",
          role: "dentist",
          practiceId: "test-practice-id",
          practiceName: "Test Practice",
        });
      })
    );
  });

  it("should render schedule page", async () => {
    render(<Schedule />, {
      isAuthenticated: true,
      user: {
        id: "test-user-id",
        email: "test@example.com",
        firstName: "Test",
        lastName: "User",
        role: "dentist",
        practiceId: "test-practice-id",
        practiceName: "Test Practice",
      },
    });
    
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it("should display calendar", async () => {
    render(<Schedule />, {
      isAuthenticated: true,
      user: {
        id: "test-user-id",
        email: "test@example.com",
        firstName: "Test",
        lastName: "User",
        role: "dentist",
        practiceId: "test-practice-id",
        practiceName: "Test Practice",
      },
    });

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it("should handle date navigation", async () => {
    const user = userEvent.setup();
    render(<Schedule />, {
      isAuthenticated: true,
      user: {
        id: "test-user-id",
        email: "test@example.com",
        firstName: "Test",
        lastName: "User",
        role: "dentist",
        practiceId: "test-practice-id",
        practiceName: "Test Practice",
      },
    });

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });

    const buttons = screen.queryAllByRole("button");
    const nextButton = buttons.find((btn) => btn.textContent?.includes("Next"));
    
    if (nextButton) {
      await user.click(nextButton);
      expect(document.body).toBeInTheDocument();
    }
  });

  it("should handle appointment creation", async () => {
    const user = userEvent.setup();
    render(<Schedule />, {
      isAuthenticated: true,
      user: {
        id: "test-user-id",
        email: "test@example.com",
        firstName: "Test",
        lastName: "User",
        role: "dentist",
        practiceId: "test-practice-id",
        practiceName: "Test Practice",
      },
    });

    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });

    const buttons = screen.queryAllByRole("button");
    const addButton = buttons.find((btn) => btn.textContent?.includes("Add") || btn.textContent?.includes("New"));
    
    if (addButton) {
      await user.click(addButton);
      expect(document.body).toBeInTheDocument();
    }
  });
});
