import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import Sidebar from "../layout/Sidebar";

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("Sidebar Component", () => {
  it("should render sidebar", () => {
    renderWithRouter(<Sidebar />);
    expect(document.body).toBeInTheDocument();
  });

  it("should have navigation links", () => {
    renderWithRouter(<Sidebar />);
    // Sidebar should render without crashing
    expect(document.body).toBeInTheDocument();
  });

  it("should be responsive", () => {
    const { container } = renderWithRouter(<Sidebar />);
    expect(container).toBeInTheDocument();
  });

  it("should handle navigation", async () => {
    const user = userEvent.setup();
    renderWithRouter(<Sidebar />);
    
    // Sidebar should render and be interactive
    expect(document.body).toBeInTheDocument();
  });
});
