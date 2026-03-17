import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  announceToScreenReader,
  generateId,
  isVisibleToScreenReader,
  getAccessibleName,
  handleArrowNavigation,
} from '@/lib/accessibility';

describe('accessibility utilities', () => {
  describe('announceToScreenReader', () => {
    it('should create announcement element', () => {
      announceToScreenReader('Test message');

      const announcement = document.querySelector('[role="status"]');
      expect(announcement).toBeTruthy();
      expect(announcement?.textContent).toBe('Test message');
    });

    it('should set aria-live priority', () => {
      announceToScreenReader('Urgent message', 'assertive');

      const announcement = document.querySelector('[aria-live="assertive"]');
      expect(announcement).toBeTruthy();
    });

    it('should remove announcement after timeout', async () => {
      announceToScreenReader('Test message');

      await new Promise((resolve) => setTimeout(resolve, 1100));

      const announcement = document.querySelector('[role="status"]');
      expect(announcement).toBeFalsy();
    });
  });

  describe('generateId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();

      expect(id1).not.toBe(id2);
    });

    it('should use custom prefix', () => {
      const id = generateId('custom');
      expect(id).toMatch(/^custom-\d+$/);
    });
  });

  describe('isVisibleToScreenReader', () => {
    let element: HTMLElement;

    beforeEach(() => {
      element = document.createElement('div');
      document.body.appendChild(element);
    });

    afterEach(() => {
      element.remove();
    });

    it('should return true for visible elements', () => {
      expect(isVisibleToScreenReader(element)).toBe(true);
    });

    it('should return false for aria-hidden elements', () => {
      element.setAttribute('aria-hidden', 'true');
      expect(isVisibleToScreenReader(element)).toBe(false);
    });
  });

  describe('getAccessibleName', () => {
    it('should get aria-label', () => {
      const element = document.createElement('button');
      element.setAttribute('aria-label', 'Close dialog');

      expect(getAccessibleName(element)).toBe('Close dialog');
    });

    it('should get text content as fallback', () => {
      const element = document.createElement('button');
      element.textContent = 'Click me';

      expect(getAccessibleName(element)).toBe('Click me');
    });
  });

  describe('handleArrowNavigation', () => {
    let items: HTMLElement[];

    beforeEach(() => {
      items = [
        document.createElement('button'),
        document.createElement('button'),
        document.createElement('button'),
      ];
      items.forEach((item) => document.body.appendChild(item));
    });

    afterEach(() => {
      items.forEach((item) => item.remove());
    });

    it('should navigate to next item with ArrowDown', () => {
      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      const newIndex = handleArrowNavigation(event, items, 0);

      expect(newIndex).toBe(1);
    });

    it('should navigate to previous item with ArrowUp', () => {
      const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
      const newIndex = handleArrowNavigation(event, items, 1);

      expect(newIndex).toBe(0);
    });

    it('should loop to start when at end', () => {
      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      const newIndex = handleArrowNavigation(event, items, 2, { loop: true });

      expect(newIndex).toBe(0);
    });

    it('should not loop when disabled', () => {
      const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
      const newIndex = handleArrowNavigation(event, items, 2, { loop: false });

      expect(newIndex).toBe(2);
    });
  });
});
