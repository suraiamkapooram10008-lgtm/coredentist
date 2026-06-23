import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import LabManagement from "../LabManagement";

describe("LabManagement Page", () => {
  it("renders the page heading and new case button", () => {
    render(
      <BrowserRouter>
        <LabManagement />
      </BrowserRouter>,
    );
    expect(
      screen.getByRole("heading", { level: 1, name: /lab management/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new case/i })).toBeInTheDocument();
  });

  it("displays summary metric cards", () => {
    render(
      <BrowserRouter>
        <LabManagement />
      </BrowserRouter>,
    );
    expect(screen.getByText("18")).toBeInTheDocument(); // Active Cases
    expect(screen.getByText(/active cases/i)).toBeInTheDocument();
  });
});
