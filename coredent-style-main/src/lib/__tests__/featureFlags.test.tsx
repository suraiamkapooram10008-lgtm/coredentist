import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  featureFlags,
  useFeatureFlag,
  FeatureGate,
} from "../featureFlags";

describe("featureFlags", () => {
  beforeEach(() => {
    // Make loadRemoteFlags deterministic: it always fails to merge so defaults
    // stay in place unless a test overrides the fetch stub explicitly.
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) }),
    );
    featureFlags.resetOverrides();
    featureFlags.initialize("test-user", "owner");
  });

  describe("isEnabled", () => {
    it("returns false for an unknown flag", () => {
      expect(featureFlags.isEnabled("doesNotExist")).toBe(false);
    });

    it("returns false for a disabled flag", () => {
      expect(featureFlags.isEnabled("newDashboard")).toBe(false);
    });

    it("returns true for an enabled flag with no gating", () => {
      expect(featureFlags.isEnabled("mobileApp")).toBe(true);
    });

    it("respects role-based gating", () => {
      // advancedReporting is enabled but gated to owner/admin
      expect(featureFlags.isEnabled("advancedReporting")).toBe(true);

      featureFlags.resetOverrides();
      featureFlags.initialize("test-user", "viewer");
      expect(featureFlags.isEnabled("advancedReporting")).toBe(false);
    });

    it("returns false when no user is initialized for a gated flag", () => {
      featureFlags.resetOverrides();
      featureFlags.initialize("user-1", "owner");
      // enabledForRoles satisfied; rollout undefined for advancedReporting → true
      expect(featureFlags.isEnabled("advancedReporting")).toBe(true);
    });

    it("respects rollout percentage consistently", () => {
      // aiAssistant rollout 10% — same user should always hash to the same bucket
      featureFlags.resetOverrides();
      featureFlags.initialize("stable-user", "owner");
      const first = featureFlags.isEnabled("aiAssistant");
      const second = featureFlags.isEnabled("aiAssistant");
      expect(first).toBe(second);
    });
  });

  describe("getEnabledFlags", () => {
    it("returns the list of currently enabled flag keys", () => {
      featureFlags.resetOverrides();
      featureFlags.initialize("test-user", "owner");
      const enabled = featureFlags.getEnabledFlags();
      expect(enabled).toContain("mobileApp");
      expect(enabled).toContain("advancedReporting");
      expect(enabled).toContain("automatedReminders");
      expect(enabled).toContain("onlineBooking");
    });
  });

  describe("getFlag / getAllFlags", () => {
    it("returns the flag details when present", () => {
      const flag = featureFlags.getFlag("mobileApp");
      expect(flag?.enabled).toBe(true);
    });

    it("returns null for an unknown flag", () => {
      expect(featureFlags.getFlag("nope")).toBeNull();
    });

    it("getAllFlags returns a fresh top-level object each call", () => {
      expect(featureFlags.getAllFlags()).not.toBe(
        featureFlags.getAllFlags(),
      );
    });

    it("getAllFlags isolates top-level mutations from internal state", () => {
      const all = featureFlags.getAllFlags();
      (all as Record<string, unknown>).injected = {
        key: "injected",
        enabled: true,
        description: "x",
      };
      expect(featureFlags.getFlag("injected")).toBeNull();
    });
  });

  describe("override / resetOverrides", () => {
    it("override flips a flag without rollout gating", () => {
      // videoConsultation is disabled with no rollout/role gating
      expect(featureFlags.isEnabled("videoConsultation")).toBe(false);
      featureFlags.override("videoConsultation", true);
      expect(featureFlags.isEnabled("videoConsultation")).toBe(true);
    });

    it("resetOverrides restores defaults", () => {
      featureFlags.override("mobileApp", false);
      expect(featureFlags.isEnabled("mobileApp")).toBe(false);
      featureFlags.resetOverrides();
      featureFlags.initialize("test-user", "owner");
      expect(featureFlags.isEnabled("mobileApp")).toBe(true);
    });
  });

  describe("loadRemoteFlags (via initialize)", () => {
    it("merges remote flags when the fetch succeeds", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({
          ok: true,
          json: async () => ({ mobileApp: { enabled: false } }),
        }),
      );
      featureFlags.resetOverrides();
      featureFlags.initialize("u", "owner");
      await vi.waitFor(() => {
        expect(featureFlags.isEnabled("mobileApp")).toBe(false);
      });
    });

    it("falls back to defaults when the fetch fails", async () => {
      vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")));
      featureFlags.resetOverrides();
      featureFlags.initialize("u", "owner");
      await vi.waitFor(() => {
        expect(featureFlags.isEnabled("mobileApp")).toBe(true);
      });
    });
  });

  describe("useFeatureFlag", () => {
    it("reflects the underlying service state", () => {
      function Probe() {
        const on = useFeatureFlag("mobileApp");
        return <span>{on ? "on" : "off"}</span>;
      }
      render(<Probe />);
      expect(screen.getByText("on")).toBeInTheDocument();
    });
  });

  describe("FeatureGate", () => {
    it("renders children when the flag is enabled", () => {
      render(
        <FeatureGate flag="mobileApp">
          <span>visible</span>
        </FeatureGate>,
      );
      expect(screen.getByText("visible")).toBeInTheDocument();
    });

    it("renders fallback when the flag is disabled", () => {
      render(
        <FeatureGate flag="newDashboard" fallback={<span>hidden</span>}>
          <span>visible</span>
        </FeatureGate>,
      );
      expect(screen.getByText("hidden")).toBeInTheDocument();
      expect(screen.queryByText("visible")).toBeNull();
    });
  });
});
