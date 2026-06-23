import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Documents from "../Documents";

describe("Documents Page", () => {
  it("renders the page heading and action buttons", () => {
    render(
      <BrowserRouter>
        <Documents />
      </BrowserRouter>,
    );
    expect(
      screen.getByRole("heading", { level: 1, name: /document management/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /new template/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create document/i })).toBeInTheDocument();
  });

  it("shows tab navigation for documents, templates, and e-signatures", () => {
    render(
      <BrowserRouter>
        <Documents />
      </BrowserRouter>,
    );
    expect(screen.getByRole("tab", { name: /documents/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /^templates$/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /e-signatures/i })).toBeInTheDocument();
  });

  it("lists default documents in the table", () => {
    render(
      <BrowserRouter>
        <Documents />
      </BrowserRouter>,
    );
    // Default tab is "documents" which shows patient documents
    expect(screen.getByText(/consent form - john smith/i)).toBeInTheDocument();
    expect(screen.getByText(/treatment plan - jane doe/i)).toBeInTheDocument();
  });
});
