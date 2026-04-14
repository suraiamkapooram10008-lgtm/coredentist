/**
 * Communications Hook
 * Custom hook for managing communications state and operations
 */

import { useState, useCallback } from 'react';
import { communicationsApi } from '@/services/communicationsApi';
import { logger } from '@/lib/logger';
import type {
  MessageTemplate,
  MessageTemplateCreate,
  MessageTemplateUpdate,
  PatientMessage,
  PatientMessageCreate,
  ReminderSchedule,
  ReminderScheduleCreate,
  ReminderScheduleUpdate,
  Conversation,
  ConversationCreate,
  ConversationMessage,
  ConversationMessageCreate,
  CommunicationSummary,
} from '@/services/communicationsApi';

interface UseCommunicationsState {
  // Templates
  templates: MessageTemplate[];
  templatesLoading: boolean;
  templatesError: string | null;

  // Messages
  messages: PatientMessage[];
  messagesLoading: boolean;
  messagesError: string | null;

  // Reminders
  reminders: ReminderSchedule[];
  remindersLoading: boolean;
  remindersError: string | null;

  // Conversations
  conversations: Conversation[];
  conversationsLoading: boolean;
  conversationsError: string | null;
  currentConversation: Conversation | null;
  conversationMessages: ConversationMessage[];

  // Summary
  summary: CommunicationSummary | null;
  summaryLoading: boolean;
  summaryError: string | null;
}

export function useCommunications() {
  const [state, setState] = useState<UseCommunicationsState>({
    templates: [],
    templatesLoading: false,
    templatesError: null,
    messages: [],
    messagesLoading: false,
    messagesError: null,
    reminders: [],
    remindersLoading: false,
    remindersError: null,
    conversations: [],
    conversationsLoading: false,
    conversationsError: null,
    currentConversation: null,
    conversationMessages: [],
    summary: null,
    summaryLoading: false,
    summaryError: null,
  });

  // Templates
  const fetchTemplates = useCallback(async (params?: { category?: string; isActive?: boolean; messageType?: string }) => {
    setState(s => ({ ...s, templatesLoading: true, templatesError: null }));
    try {
      const result = await communicationsApi.templates.list(params);
      if (result.success && result.data) {
        setState(s => ({ ...s, templates: result.data || [], templatesLoading: false }));
      } else {
        setState(s => ({ ...s, templatesLoading: false, templatesError: result.error?.message || 'Failed to fetch templates' }));
      }
    } catch (error) {
      logger.error('Failed to send conversation message', error as Error);
      return null;
    }
  }, []);

  const createTemplate = useCallback(async (template: MessageTemplateCreate) => {
    setState(s => ({ ...s, templatesLoading: true, templatesError: null }));
    try {
      const result = await communicationsApi.templates.create(template);
      if (result.success && result.data) {
        setState(s => ({ ...s, templates: [...s.templates, result.data!], templatesLoading: false }));
        return result.data;
      } else {
        setState(s => ({ ...s, templatesLoading: false, templatesError: result.error?.message || 'Failed to create template' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to create template', error as Error);
      setState(s => ({ ...s, templatesLoading: false, templatesError: 'An error occurred while creating template' }));
      return null;
    }
  }, []);

  const updateTemplate = useCallback(async (templateId: string, template: MessageTemplateUpdate) => {
    setState(s => ({ ...s, templatesLoading: true, templatesError: null }));
    try {
      const result = await communicationsApi.templates.update(templateId, template);
      if (result.success && result.data) {
        setState(s => ({
          ...s,
          templates: s.templates.map(t => t.id === templateId ? result.data! : t),
          templatesLoading: false,
        }));
        return result.data;
      } else {
        setState(s => ({ ...s, templatesLoading: false, templatesError: result.error?.message || 'Failed to update template' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to update template', error as Error);
      setState(s => ({ ...s, templatesLoading: false, templatesError: 'An error occurred while updating template' }));
      return null;
    }
  }, []);

  const deleteTemplate = useCallback(async (templateId: string) => {
    setState(s => ({ ...s, templatesLoading: true, templatesError: null }));
    try {
      const result = await communicationsApi.templates.delete(templateId);
      if (result.success) {
        setState(s => ({
          ...s,
          templates: s.templates.filter(t => t.id !== templateId),
          templatesLoading: false,
        }));
        return true;
      } else {
        setState(s => ({ ...s, templatesLoading: false, templatesError: result.error?.message || 'Failed to delete template' }));
        return false;
      }
    } catch (error) {
      logger.error('Failed to delete template', error as Error);
      setState(s => ({ ...s, templatesLoading: false, templatesError: 'An error occurred while deleting template' }));
      return false;
    }
  }, []);

  // Messages
  const fetchMessages = useCallback(async (params?: {
    patientId?: string;
    messageType?: string;
    status?: string;
    direction?: string;
    dateFrom?: string;
    dateTo?: string;
  }) => {
    setState(s => ({ ...s, messagesLoading: true, messagesError: null }));
    try {
      const result = await communicationsApi.messages.list(params);
      if (result.success && result.data) {
        setState(s => ({ ...s, messages: result.data || [], messagesLoading: false }));
      } else {
        setState(s => ({ ...s, messagesLoading: false, messagesError: result.error?.message || 'Failed to fetch messages' }));
      }
    } catch (error) {
      logger.error('Failed to fetch messages', error as Error);
      setState(s => ({ ...s, messagesLoading: false, messagesError: 'An error occurred while fetching messages' }));
    }
  }, []);

  const sendMessage = useCallback(async (message: PatientMessageCreate) => {
    setState(s => ({ ...s, messagesLoading: true, messagesError: null }));
    try {
      const result = await communicationsApi.messages.send(message);
      if (result.success && result.data) {
        setState(s => ({ ...s, messages: [...s.messages, result.data!], messagesLoading: false }));
        return result.data;
      } else {
        setState(s => ({ ...s, messagesLoading: false, messagesError: result.error?.message || 'Failed to send message' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to send message', error as Error);
      setState(s => ({ ...s, messagesLoading: false, messagesError: 'An error occurred while sending message' }));
      return null;
    }
  }, []);

  // Reminders
  const fetchReminders = useCallback(async (params?: { isActive?: boolean; reminderType?: string }) => {
    setState(s => ({ ...s, remindersLoading: true, remindersError: null }));
    try {
      const result = await communicationsApi.reminders.list(params);
      if (result.success && result.data) {
        setState(s => ({ ...s, reminders: result.data || [], remindersLoading: false }));
      } else {
        setState(s => ({ ...s, remindersLoading: false, remindersError: result.error?.message || 'Failed to fetch reminders' }));
      }
    } catch (error) {
      logger.error('Failed to fetch reminders', error as Error);
      setState(s => ({ ...s, remindersLoading: false, remindersError: 'An error occurred while fetching reminders' }));
    }
  }, []);

  const createReminder = useCallback(async (reminder: ReminderScheduleCreate) => {
    setState(s => ({ ...s, remindersLoading: true, remindersError: null }));
    try {
      const result = await communicationsApi.reminders.create(reminder);
      if (result.success && result.data) {
        setState(s => ({ ...s, reminders: [...s.reminders, result.data!], remindersLoading: false }));
        return result.data;
      } else {
        setState(s => ({ ...s, remindersLoading: false, remindersError: result.error?.message || 'Failed to create reminder' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to create reminder', error as Error);
      setState(s => ({ ...s, remindersLoading: false, remindersError: 'An error occurred while creating reminder' }));
      return null;
    }
  }, []);

  const updateReminder = useCallback(async (reminderId: string, reminder: ReminderScheduleUpdate) => {
    setState(s => ({ ...s, remindersLoading: true, remindersError: null }));
    try {
      const result = await communicationsApi.reminders.update(reminderId, reminder);
      if (result.success && result.data) {
        setState(s => ({
          ...s,
          reminders: s.reminders.map(r => r.id === reminderId ? result.data! : r),
          remindersLoading: false,
        }));
        return result.data;
      } else {
        setState(s => ({ ...s, remindersLoading: false, remindersError: result.error?.message || 'Failed to update reminder' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to update reminder', error as Error);
      setState(s => ({ ...s, remindersLoading: false, remindersError: 'An error occurred while updating reminder' }));
      return null;
    }
  }, []);

  const deleteReminder = useCallback(async (reminderId: string) => {
    setState(s => ({ ...s, remindersLoading: true, remindersError: null }));
    try {
      const result = await communicationsApi.reminders.delete(reminderId);
      if (result.success) {
        setState(s => ({
          ...s,
          reminders: s.reminders.filter(r => r.id !== reminderId),
          remindersLoading: false,
        }));
        return true;
      } else {
        setState(s => ({ ...s, remindersLoading: false, remindersError: result.error?.message || 'Failed to delete reminder' }));
        return false;
      }
    } catch (error) {
      logger.error('Failed to delete reminder', error as Error);
      setState(s => ({ ...s, remindersLoading: false, remindersError: 'An error occurred while deleting reminder' }));
      return false;
    }
  }, []);

  // Conversations
  const fetchConversations = useCallback(async (params?: { status?: string; patientId?: string }) => {
    setState(s => ({ ...s, conversationsLoading: true, conversationsError: null }));
    try {
      const result = await communicationsApi.conversations.list(params);
      if (result.success && result.data) {
        setState(s => ({ ...s, conversations: result.data || [], conversationsLoading: false }));
      } else {
        setState(s => ({ ...s, conversationsLoading: false, conversationsError: result.error?.message || 'Failed to fetch conversations' }));
      }
    } catch (error) {
      logger.error('Failed to fetch conversations', error as Error);
      setState(s => ({ ...s, conversationsLoading: false, conversationsError: 'An error occurred while fetching conversations' }));
    }
  }, []);

  const selectConversation = useCallback(async (conversationId: string) => {
    setState(s => ({ ...s, conversationsLoading: true, conversationsError: null }));
    try {
      const result = await communicationsApi.conversations.get(conversationId);
      if (result.success && result.data) {
        setState(s => ({ ...s, currentConversation: result.data!, conversationsLoading: false }));
        // Also fetch messages for this conversation
        const messagesResult = await communicationsApi.conversations.getMessages(conversationId);
        if (messagesResult.success && messagesResult.data) {
          setState(s => ({ ...s, conversationMessages: messagesResult.data || [] }));
        }
        return result.data;
      } else {
        setState(s => ({ ...s, conversationsLoading: false, conversationsError: result.error?.message || 'Failed to fetch conversation' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to fetch conversation', error as Error);
      setState(s => ({ ...s, conversationsLoading: false, conversationsError: 'An error occurred while fetching conversation' }));
      return null;
    }
  }, []);

  const createConversation = useCallback(async (conversation: ConversationCreate) => {
    setState(s => ({ ...s, conversationsLoading: true, conversationsError: null }));
    try {
      const result = await communicationsApi.conversations.create(conversation);
      if (result.success && result.data) {
        setState(s => ({ ...s, conversations: [...s.conversations, result.data!], conversationsLoading: false }));
        return result.data;
      } else {
        setState(s => ({ ...s, conversationsLoading: false, conversationsError: result.error?.message || 'Failed to create conversation' }));
        return null;
      }
    } catch (error) {
      logger.error('Failed to create conversation', error as Error);
      setState(s => ({ ...s, conversationsLoading: false, conversationsError: 'An error occurred while creating conversation' }));
      return null;
    }
  }, []);

  const sendConversationMessage = useCallback(async (conversationId: string, message: ConversationMessageCreate) => {
    try {
      const result = await communicationsApi.conversations.sendMessage(conversationId, message);
      if (result.success && result.data) {
        setState(s => ({
          ...s,
          conversationMessages: [...s.conversationMessages, result.data!],
        }));
        return result.data;
      } else {
        logger.error('Failed to send conversation message', new Error(result.error?.message || 'Unknown error'));
        return null;
      }
    } catch (error) {
      logger.error('Failed to send conversation message', error as Error);
      return null;
    }
  }, []);

  // Summary
  const fetchSummary = useCallback(async () => {
    setState(s => ({ ...s, summaryLoading: true, summaryError: null }));
    try {
      const result = await communicationsApi.getSummary();
      if (result.success && result.data) {
        setState(s => ({ ...s, summary: result.data!, summaryLoading: false }));
      } else {
        setState(s => ({ ...s, summaryLoading: false, summaryError: result.error?.message || 'Failed to fetch summary' }));
      }
    } catch (error) {
      logger.error('Failed to fetch summary', error as Error);
      setState(s => ({ ...s, summaryLoading: false, summaryError: 'An error occurred while fetching summary' }));
    }
  }, []);

  return {
    ...state,
    // Templates
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    // Messages
    fetchMessages,
    sendMessage,
    // Reminders
    fetchReminders,
    createReminder,
    updateReminder,
    deleteReminder,
    // Conversations
    fetchConversations,
    selectConversation,
    createConversation,
    sendConversationMessage,
    // Summary
    fetchSummary,
  };
}