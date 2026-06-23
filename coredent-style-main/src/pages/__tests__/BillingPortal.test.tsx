import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import BillingPortal from "../BillingPortal";

describe("BillingPortal Page", () => {
  it("renders the page heading", () => {
    render(
      <BrowserRouter>
        <BillingPortal />
      </BrowserRouter>,
    );
    expect(screen.getByText(/intelligent billing/i)).toBeInTheDocument();
  });

  it("shows payment plan data in the default tab", () => {
    render(
      <BrowserRouter>
        <BillingPortal />
      </BrowserRouter>,
    );
    // Default tab is "Active Payment Plans" — "Sarah Wilson" appears in both h3 and p
    expect(screen.getAllByText(/sarah wilson/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/PLN-9901/i)).toBeInTheDocument();
  });
});
