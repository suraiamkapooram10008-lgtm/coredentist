import { describe, it, expect } from "vitest";
import { apiClient, authApi, patientsApi, appointmentsApi } from "../api";

describe("API Client", () => {
  describe("apiClient", () => {
    it("should be defined", () => {
      expect(apiClient).toBeDefined();
    });

    it("should have expected methods", () => {
      expect(typeof apiClient.get).toBe("function");
      expect(typeof apiClient.post).toBe("function");
      expect(typeof apiClient.put).toBe("function");
      expect(typeof apiClient.delete).toBe("function");
    });
  });

  describe("authApi", () => {
    it("should have auth methods", () => {
      expect(typeof authApi.login).toBe("function");
      expect(typeof authApi.logout).toBe("function");
      expect(typeof authApi.getCurrentUser).toBe("function");
    });
  });

  describe("patientsApi", () => {
    it("should have patient methods", () => {
      expect(typeof patientsApi.list).toBe("function");
      expect(typeof patientsApi.getById).toBe("function");
      expect(typeof patientsApi.create).toBe("function");
      expect(typeof patientsApi.update).toBe("function");
      expect(typeof patientsApi.delete).toBe("function");
    });
  });

  describe("appointmentsApi", () => {
    it("should have appointment methods", () => {
      expect(typeof appointmentsApi.list).toBe("function");
      expect(typeof appointmentsApi.getById).toBe("function");
      expect(typeof appointmentsApi.create).toBe("function");
      expect(typeof appointmentsApi.update).toBe("function");
      expect(typeof appointmentsApi.delete).toBe("function");
    });
  });
});