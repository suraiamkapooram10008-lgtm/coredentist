import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import BookingSuccess from "../BookingSuccess";

describe("BookingSuccess Page", () => {
  it("renders the success heading and practice name", () => {
    render(
      <BrowserRouter>
        <BookingSuccess />
      </BrowserRouter>,
    );
    expect(screen.getByText(/booking requested/i)).toBeInTheDocument();
    expect(screen.getByText(/coredent family dental/i)).toBeInTheDocument();
  });

  it("has a return home button", () => {
    render(
      <BrowserRouter>
        <BookingSuccess />
      </BrowserRouter>,
    );
    expect(screen.getByRole("button", { name: /return home/i })).toBeInTheDocument();
  });
});
