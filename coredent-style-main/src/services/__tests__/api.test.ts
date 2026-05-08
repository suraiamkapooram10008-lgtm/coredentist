import { describe, it, expect, beforeEach, vi } from "vitest";
import { apiClient, setAuthToken, clearAuthToken } from "../api";

describe("API Client", () => {
  beforeEach(() => {
    clearAuthToken();
    vi.clearAllMocks();
  });

  describe("setAuthToken", () => {
    it("should set auth token", () => {
      setAuthToken("test-token");
      expect(localStorage.getItem("auth_token")).toBe("test-token");
    });
  });

  describe("clearAuthToken", () => {
    it("should clear auth token", () => {
      setAuthToken("test-token");
      clearAuthToken();
      expect(localStorage.getItem("auth_token")).toBeNull();
    });
  });

  describe("apiClient", () => {
    it("should be defined", () => {
      expect(apiClient).toBeDefined();
    });

    it("should have base URL configured", () => {
      expect(apiClient.defaults.baseURL).toBeDefined();
    });

    it("should have interceptors configured", () => {
      expect(apiClient.interceptors).toBeDefined();
    });
  });
});
