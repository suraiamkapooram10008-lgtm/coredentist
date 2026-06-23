import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Inventory from "../Inventory";

describe("Inventory Page", () => {
  it("renders the page heading and add button", () => {
    render(
      <BrowserRouter>
        <Inventory />
      </BrowserRouter>,
    );
    expect(
      screen.getByRole("heading", { level: 1, name: /inventory management/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /add item/i }),
    ).toBeInTheDocument();
  });

  it("displays summary cards with expected metrics", () => {
    render(
      <BrowserRouter>
        <Inventory />
      </BrowserRouter>,
    );
    // Verify the actual metric values are rendered
    expect(screen.getByText("248")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("236")).toBeInTheDocument();
  });

  it("renders inventory table with static items", () => {
    render(
      <BrowserRouter>
        <Inventory />
      </BrowserRouter>,
    );
    expect(screen.getByText(/disposable gloves/i)).toBeInTheDocument();
    expect(screen.getByText(/dental mirror/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search by name or sku/i)).toBeInTheDocument();
  });
});
