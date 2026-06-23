import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import RevenueLanding from "../RevenueLanding";
import ReferralHub from "../ReferralHub";
import ImagingHub from "../ImagingHub";

describe("RevenueLanding Page", () => {
  it("renders the page heading", () => {
    render(<BrowserRouter><RevenueLanding /></BrowserRouter>);
    expect(screen.getByText(/revenue cycle hub/i)).toBeInTheDocument();
  });
});

describe("ReferralHub Page", () => {
  it("renders the page heading", () => {
    render(<BrowserRouter><ReferralHub /></BrowserRouter>);
    expect(screen.getByText(/inter-practice referral hub/i)).toBeInTheDocument();
  });
});

describe("ImagingHub Page", () => {
  it("renders the page heading", () => {
    render(<BrowserRouter><ImagingHub /></BrowserRouter>);
    expect(screen.getByText(/pacs & imaging hub/i)).toBeInTheDocument();
  });
});
