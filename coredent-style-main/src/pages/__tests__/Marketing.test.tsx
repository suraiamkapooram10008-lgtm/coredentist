import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Marketing from "../Marketing";

describe("Marketing Page", () => {
  it("renders the page heading and new campaign button", () => {
    render(
      <BrowserRouter>
        <Marketing />
      </BrowserRouter>,
    );
    expect(
      screen.getByRole("heading", { level: 1, name: /marketing/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new campaign/i })).toBeInTheDocument();
  });

  it("renders campaign data in the default tab table", () => {
    render(
      <BrowserRouter>
        <Marketing />
      </BrowserRouter>,
    );
    // Default tab is "campaigns"
    expect(screen.getByText(/spring cleaning special/i)).toBeInTheDocument();
    expect(screen.getByText(/new patient welcome/i)).toBeInTheDocument();
  });

  it("shows tab navigation", () => {
    render(
      <BrowserRouter>
        <Marketing />
      </BrowserRouter>,
    );
    expect(screen.getByRole("tab", { name: /campaigns/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /patient segments/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /analytics/i })).toBeInTheDocument();
  });
});
