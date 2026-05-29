import { describe, it, expect, beforeEach, vi } from "vitest";
import { apiClient, authApi } from "../api";

describe("API Client", () => {
  beforeEach(() => {
    apiClient.setToken(null);
    vi.clearAllMocks();
  });

  describe("token management", () => {
    it("should set and get auth token", () => {
      apiClient.setToken("test-token");
      expect(apiClient.getToken()).toBe("test-token");
    });

    it("should clear auth token", () => {
      apiClient.setToken("test-token");
      apiClient.setToken(null);
      expect(apiClient.getToken()).toBeNull();
    });
  });

  describe("apiClient", () => {
    it("should be defined", () => {
      expect(apiClient).toBeDefined();
    });

    it("should have get method", () => {
      expect(typeof apiClient.get).toBe("function");
    });

    it("should have post method", () => {
      expect(typeof apiClient.post).toBe("function");
    });
  });

  describe("authApi", () => {
    it("should have login method", () => {
      expect(typeof authApi.login).toBe("function");
    });

    it("should have logout method", () => {
      expect(typeof authApi.logout).toBe("function");
    });

    it("should have getCurrentUser method", () => {
      expect(typeof authApi.getCurrentUser).toBe("function");
    });
  });
});
