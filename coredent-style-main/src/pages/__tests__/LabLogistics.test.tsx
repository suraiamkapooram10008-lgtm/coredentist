import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import LabLogistics from "../LabLogistics";

describe("LabLogistics Page", () => {
  it("renders the page heading", () => {
    render(
      <BrowserRouter>
        <LabLogistics />
      </BrowserRouter>,
    );
    expect(screen.getByText(/lab logistics hub/i)).toBeInTheDocument();
  });
});
