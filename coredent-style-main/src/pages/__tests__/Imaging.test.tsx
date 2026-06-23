import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Imaging from "../Imaging";

describe("Imaging Page", () => {
  it("renders the page heading and upload button", () => {
    render(
      <BrowserRouter>
        <Imaging />
      </BrowserRouter>,
    );
    expect(
      screen.getByRole("heading", { level: 1, name: /imaging/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /upload image/i })).toBeInTheDocument();
  });

  it("renders study data in the table", () => {
    render(
      <BrowserRouter>
        <Imaging />
      </BrowserRouter>,
    );
    expect(screen.getByText(/john smith/i)).toBeInTheDocument();
    expect(screen.getByText(/x-ray \(pa\)/i)).toBeInTheDocument();
  });
});
