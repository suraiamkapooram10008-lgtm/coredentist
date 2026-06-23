import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import EnterpriseHQ from "../EnterpriseHQ";

describe("EnterpriseHQ Page", () => {
  it("renders the page heading", () => {
    render(
      <BrowserRouter>
        <EnterpriseHQ />
      </BrowserRouter>,
    );
    expect(screen.getByText(/enterprise hq dashboard/i)).toBeInTheDocument();
  });
});
