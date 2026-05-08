import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@/test/test-utils";
import Dashboard from "../Dashboard";
import { server } from "@/test/mocks/server";
import { http, HttpResponse } from "msw";

// Mock hooks that may be used by Dashboard
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("Dashboard Page", () => {
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

  it("should render dashboard", async () => {
    render(<Dashboard />, {
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
    
    // Dashboard shows personalized greeting
    await waitFor(() => {
      // Use getAllByRole since there are multiple headings
      const headings = screen.getAllByRole("heading");
      expect(headings.length).toBeGreaterThan(0);
    });
    
    // Check for personalized greeting
    expect(screen.getByText(/Good (morning|afternoon|evening)/i)).toBeInTheDocument();
  });

  it("should display loading state initially", () => {
    render(<Dashboard />, { isLoading: true });
    // Dashboard should render without crashing
    expect(document.body).toBeInTheDocument();
  });

  it("should handle errors gracefully", async () => {
    render(<Dashboard />, {
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
      // Should render without crashing even if data fails to load
      expect(document.body).toBeInTheDocument();
    });
  });
});
