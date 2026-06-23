import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ForgotPassword from "../ForgotPassword";

describe("ForgotPassword Page", () => {
  it("renders branding and email input", () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: /coredent/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it("has a link back to login", () => {
    render(
      <BrowserRouter>
        <ForgotPassword />
      </BrowserRouter>,
    );
    const loginLink = screen.getByRole("link", { name: /back to login/i });
    expect(loginLink).toHaveAttribute("href", "/login");
  });
});
