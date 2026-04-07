import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useApi } from "../useApi";

describe("useApi Hook", () => {
  it("should initialize with loading state", () => {
    const { result } = renderHook(() => useApi("/test"));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("should handle successful data fetch", async () => {
    const mockData = { id: 1, name: "Test" };
    
    const { result } = renderHook(() => useApi("/test"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("should handle errors", async () => {
    const { result } = renderHook(() => useApi("/invalid-endpoint"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("should refetch data when calling refetch", async () => {
    const { result } = renderHook(() => useApi("/test"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    result.current.refetch();
    expect(result.current.loading).toBe(true);
  });
});
