import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "../ui/button";

describe("Button Component", () => {
  it("should render button with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("should handle click events", async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    await userEvent.click(screen.getByText("Click me"));
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it("should be disabled when disabled prop is true", () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText("Click me")).toBeDisabled();
  });

  it("should support different variants", () => {
    const { container } = render(<Button variant="outline">Click me</Button>);
    expect(container.querySelector("button")).toBeInTheDocument();
  });

  it("should support different sizes", () => {
    const { container } = render(<Button size="lg">Click me</Button>);
    expect(container.querySelector("button")).toBeInTheDocument();
  });

  it("should show loading state", () => {
    render(<Button disabled>Loading...</Button>);
    expect(screen.getByText("Loading...")).toBeDisabled();
  });
});
