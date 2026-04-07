import { describe, it, expect } from "vitest";
import {
  cn,
  formatDate,
  formatCurrency,
  formatPhoneNumber,
  validateEmail,
  truncateText,
  debounce,
  throttle,
  getInitials,
  capitalizeWords,
  slugify,
  parseJwt,
  isValidUUID,
  getErrorMessage,
  sleep,
  retry,
} from "../utils";

describe("Utils", () => {
  describe("cn", () => {
    it("should merge class names", () => {
      expect(cn("px-2", "py-1")).toBe("px-2 py-1");
    });

    it("should handle conditional classes", () => {
      expect(cn("px-2", false && "py-1")).toBe("px-2");
    });

    it("should handle undefined and null", () => {
      expect(cn("px-2", undefined, null, "py-1")).toBe("px-2 py-1");
    });
  });

  describe("formatDate", () => {
    it("should format date correctly", () => {
      const date = new Date("2026-04-07");
      const result = formatDate(date);
      expect(result).toContain("2026");
    });

    it("should handle string dates", () => {
      const result = formatDate("2026-04-07");
      expect(result).toContain("2026");
    });
  });

  describe("formatCurrency", () => {
    it("should format currency with default USD", () => {
      expect(formatCurrency(100)).toContain("100");
    });

    it("should format currency with custom currency", () => {
      const result = formatCurrency(100, "EUR");
      expect(result).toContain("100");
    });

    it("should handle decimal values", () => {
      const result = formatCurrency(99.99);
      expect(result).toContain("99.99");
    });
  });

  describe("formatPhoneNumber", () => {
    it("should format US phone number", () => {
      const result = formatPhoneNumber("1234567890");
      expect(result).toMatch(/\d/);
    });

    it("should handle short numbers", () => {
      const result = formatPhoneNumber("123");
      expect(result).toBe("123");
    });
  });

  describe("validateEmail", () => {
    it("should validate correct email", () => {
      expect(validateEmail("test@example.com")).toBe(true);
    });

    it("should reject invalid email", () => {
      expect(validateEmail("invalid-email")).toBe(false);
    });

    it("should reject empty string", () => {
      expect(validateEmail("")).toBe(false);
    });
  });

  describe("truncateText", () => {
    it("should truncate long text", () => {
      const result = truncateText("This is a long text", 10);
      expect(result.length).toBeLessThanOrEqual(13); // 10 + "..."
    });

    it("should not truncate short text", () => {
      const result = truncateText("Short", 10);
      expect(result).toBe("Short");
    });
  });

  describe("debounce", () => {
    it("should debounce function calls", async () => {
      let callCount = 0;
      const fn = debounce(() => {
        callCount++;
      }, 50);

      fn();
      fn();
      fn();

      await sleep(100);
      expect(callCount).toBe(1);
    });
  });

  describe("throttle", () => {
    it("should throttle function calls", async () => {
      let callCount = 0;
      const fn = throttle(() => {
        callCount++;
      }, 50);

      fn();
      fn();
      fn();

      await sleep(100);
      expect(callCount).toBeGreaterThan(0);
    });
  });

  describe("getInitials", () => {
    it("should get initials from name", () => {
      expect(getInitials("John Doe")).toBe("JD");
    });

    it("should handle single name", () => {
      expect(getInitials("John")).toBe("J");
    });

    it("should handle empty string", () => {
      expect(getInitials("")).toBe("");
    });
  });

  describe("capitalizeWords", () => {
    it("should capitalize words", () => {
      expect(capitalizeWords("hello world")).toBe("Hello World");
    });

    it("should handle single word", () => {
      expect(capitalizeWords("hello")).toBe("Hello");
    });
  });

  describe("slugify", () => {
    it("should convert to slug", () => {
      expect(slugify("Hello World")).toBe("hello-world");
    });

    it("should handle special characters", () => {
      const result = slugify("Hello & World!");
      expect(result).not.toContain(" ");
    });
  });

  describe("isValidUUID", () => {
    it("should validate UUID", () => {
      const uuid = "550e8400-e29b-41d4-a716-446655440000";
      expect(isValidUUID(uuid)).toBe(true);
    });

    it("should reject invalid UUID", () => {
      expect(isValidUUID("not-a-uuid")).toBe(false);
    });
  });

  describe("getErrorMessage", () => {
    it("should extract error message from Error object", () => {
      const error = new Error("Test error");
      expect(getErrorMessage(error)).toBe("Test error");
    });

    it("should handle string errors", () => {
      expect(getErrorMessage("String error")).toBe("String error");
    });

    it("should handle unknown errors", () => {
      expect(getErrorMessage({})).toBe("An unknown error occurred");
    });
  });

  describe("sleep", () => {
    it("should delay execution", async () => {
      const start = Date.now();
      await sleep(50);
      const elapsed = Date.now() - start;
      expect(elapsed).toBeGreaterThanOrEqual(40);
    });
  });

  describe("retry", () => {
    it("should retry failed function", async () => {
      let attempts = 0;
      const fn = async () => {
        attempts++;
        if (attempts < 2) throw new Error("Failed");
        return "success";
      };

      const result = await retry(fn, { maxAttempts: 3, delay: 10 });
      expect(result).toBe("success");
      expect(attempts).toBe(2);
    });

    it("should throw after max attempts", async () => {
      const fn = async () => {
        throw new Error("Always fails");
      };

      await expect(retry(fn, { maxAttempts: 2, delay: 10 })).rejects.toThrow();
    });
  });
});
