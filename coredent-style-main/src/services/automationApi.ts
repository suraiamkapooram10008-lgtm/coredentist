// ============================================
// CoreDent PMS - Automation API Service
// Handles n8n webhook triggers and configuration
// ============================================

import type {
  AutomationWebhook,
  AutomationEvent,
  AutomationPayload,
} from '@/types/automation';
import { apiClient } from './api';

export const automationApi = {
  // Get all configured webhooks
  getWebhooks: async (): Promise<AutomationWebhook[]> => {
    const response = await apiClient.get<AutomationWebhook[]>('/automations/webhooks');
    return response.success && response.data ? response.data : [];
  },

  // Get webhooks for a specific event
  getWebhooksByEvent: async (event: AutomationEvent): Promise<AutomationWebhook[]> => {
    const response = await apiClient.get<AutomationWebhook[]>('/automations/webhooks', { event });
    return response.success && response.data ? response.data : [];
  },

  // Create a new webhook
  createWebhook: async (
    data: Omit<AutomationWebhook, 'id' | 'createdAt' | 'updatedAt'>
  ): Promise<AutomationWebhook> => {
    const response = await apiClient.post<AutomationWebhook>('/automations/webhooks', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create webhook');
  },

  // Update a webhook
  updateWebhook: async (
    id: string,
    data: Partial<AutomationWebhook>
  ): Promise<AutomationWebhook> => {
    const response = await apiClient.put<AutomationWebhook>(`/automations/webhooks/${id}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update webhook');
  },

  // Delete a webhook
  deleteWebhook: async (id: string): Promise<void> => {
    await apiClient.delete<void>(`/automations/webhooks/${id}`);
  },

  // Toggle webhook active status
  toggleWebhook: async (id: string): Promise<AutomationWebhook> => {
    const response = await apiClient.post<AutomationWebhook>(`/automations/webhooks/${id}/toggle`);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to toggle webhook');
  },

  // Trigger a webhook (call n8n)
  triggerWebhook: async (
    event: AutomationEvent,
    payload: AutomationPayload
  ): Promise<{ success: boolean; triggeredCount: number }> => {
    const response = await apiClient.post<{ success: boolean; triggeredCount: number }>(
      '/automations/trigger',
      { event, payload }
    );
    return response.success && response.data ? response.data : { success: false, triggeredCount: 0 };
  },

  // Test a webhook connection
  testWebhook: async (webhookUrl: string, secretToken?: string): Promise<boolean> => {
    const response = await apiClient.post<{ success: boolean }>('/automations/test', {
      webhookUrl,
      secretToken,
    });
    return response.success && response.data ? response.data.success : false;
  },
};

// Helper function to trigger automation from anywhere in the app
export async function triggerAutomation(
  event: AutomationEvent,
  payload: AutomationPayload
): Promise<void> {
  await automationApi.triggerWebhook(event, payload);
}
