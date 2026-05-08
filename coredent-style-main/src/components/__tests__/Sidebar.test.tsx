import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Sidebar } from "../layout/Sidebar";

describe("Sidebar Component", () => {
  const mockToggle = vi.fn();
  const mockMobileClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render sidebar with navigation items", async () => {
    render(
      <TooltipProvider>
        <Sidebar 
          collapsed={false} 
          mobileOpen={false} 
          onToggle={mockToggle} 
          onMobileClose={mockMobileClose} 
        />
      </TooltipProvider>,
      {
        isAuthenticated: true,
        user: {
          id: "test-user-id",
          email: "test@example.com",
          firstName: "Test",
          lastName: "User",
          role: "admin",
          practiceId: "test-practice-id",
          practiceName: "Test Practice",
        },
      }
    );
    
    // There are two sidebars (desktop and mobile), so use getAllByText
    await waitFor(() => {
      expect(screen.getAllByText("CoreDent").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Dashboard").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Patients").length).toBeGreaterThan(0);
    });
  });

  it("should have navigation links for admin user", async () => {
    render(
      <TooltipProvider>
        <Sidebar 
          collapsed={false} 
          mobileOpen={false} 
          onToggle={mockToggle} 
          onMobileClose={mockMobileClose} 
        />
      </TooltipProvider>,
      {
        isAuthenticated: true,
        user: {
          id: "test-user-id",
          email: "test@example.com",
          firstName: "Test",
          lastName: "User",
          role: "admin",
          practiceId: "test-practice-id",
          practiceName: "Test Practice",
        },
      }
    );
    
    // Admin should see admin-only items like Reports and Settings
    await waitFor(() => {
      expect(screen.getAllByText("Reports").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Settings").length).toBeGreaterThan(0);
    });
  });

  it("should show collapsed state properly", async () => {
    render(
      <TooltipProvider>
        <Sidebar 
          collapsed={true} 
          mobileOpen={false} 
          onToggle={mockToggle} 
          onMobileClose={mockMobileClose} 
        />
      </TooltipProvider>,
      {
        isAuthenticated: true,
        user: {
          id: "test-user-id",
          email: "test@example.com",
          firstName: "Test",
          lastName: "User",
          role: "admin",
          practiceId: "test-practice-id",
          practiceName: "Test Practice",
        },
      }
    );
    
    // When collapsed, sidebar still has navigation links (shown as icons)
    await waitFor(() => {
      const links = screen.getAllByRole("link");
      expect(links.length).toBeGreaterThan(0);
    });
  });

  it("should show collapse button and handle click", async () => {
    const user = userEvent.setup();
    
    render(
      <TooltipProvider>
        <Sidebar 
          collapsed={false} 
          mobileOpen={false} 
          onToggle={mockToggle} 
          onMobileClose={mockMobileClose} 
        />
      </TooltipProvider>,
      {
        isAuthenticated: true,
        user: {
          id: "test-user-id",
          email: "test@example.com",
          firstName: "Test",
          lastName: "User",
          role: "admin",
          practiceId: "test-practice-id",
          practiceName: "Test Practice",
        },
      }
    );
    
    await waitFor(() => {
      expect(screen.getAllByText("Collapse").length).toBeGreaterThan(0);
    });
    
    const collapseButtons = screen.getAllByText("Collapse");
    const collapseButton = collapseButtons[0].closest("button");
    if (collapseButton) {
      await user.click(collapseButton);
      expect(mockToggle).toHaveBeenCalled();
    }
  });
});
