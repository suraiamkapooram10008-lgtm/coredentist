// ============================================
// CoreDent PMS - useCommunications Hook
// ============================================

import { useState, useCallback } from 'react';
import { apiClient } from '@/services/api';

export interface MessageTemplate {
  id: string;
  name: string;
  messageType: 'sms' | 'email';
  subject?: string;
  content: string;
  category: string;
  variables: string[];
  isActive: boolean;
  isDefault: boolean;
}

export interface ReminderSchedule {
  id: string;
  name: string;
  reminderType: 'appointment' | 'recall' | 'treatment';
  daysBefore: number;
  hoursBefore: number;
  minutesBefore: number;
  messageType: 'sms' | 'email';
  isActive: boolean;
  sendOnWeekends: boolean;
  maxReminders: number;
  templateId: string;
}

export interface Conversation {
  id: string;
  patientId: string;
  lastMessagePreview?: string;
  lastMessageAt?: string;
  unreadCount: number;
  channel: 'sms' | 'email';
}

export interface ConversationMessage {
  id: string;
  conversationId: string;
  senderType: 'patient' | 'staff' | 'system';
  content: string;
  createdAt: string;
}

export interface CommunicationSummary {
  unreadMessages: number;
  messages: {
    totalSent: number;
    deliveryRate: number;
  };
  reminders: {
    pending: number;
  };
}

export function useCommunications() {
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);

  const [reminders, setReminders] = useState<ReminderSchedule[]>([]);
  const [remindersLoading, setRemindersLoading] = useState(false);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);

  const [conversationMessages, setConversationMessages] = useState<ConversationMessage[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);

  const [summary, setSummary] = useState<CommunicationSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  // --- Templates ---
  const fetchTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const response = await apiClient.get<MessageTemplate[]>('/communications/templates');
      if (response.success && response.data) {
        setTemplates(response.data);
      } else {
        setTemplates([]);
      }
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  const createTemplate = async (template: Omit<MessageTemplate, 'id'>) => {
    const response = await apiClient.post<MessageTemplate>('/communications/templates', template);
    if (!response.success || !response.data) throw new Error("Failed to create message template");
    const newTemplate = response.data;
    setTemplates(prev => [...prev, newTemplate]);
    return newTemplate;
  };

  const updateTemplate = async (id: string, template: Partial<MessageTemplate>) => {
    await apiClient.put<MessageTemplate>(`/communications/templates/${id}`, template);
    setTemplates(prev => prev.map(t => t.id === id ? { ...t, ...template } : t));
  };

  const deleteTemplate = async (id: string) => {
    await apiClient.delete<void>(`/communications/templates/${id}`);
    setTemplates(prev => prev.filter(t => t.id !== id));
  };

  // --- Reminders ---
  const fetchReminders = useCallback(async () => {
    setRemindersLoading(true);
    try {
      const response = await apiClient.get<ReminderSchedule[]>('/communications/reminders');
      if (response.success && response.data) {
        setReminders(response.data);
      } else {
        setReminders([]);
      }
    } finally {
      setRemindersLoading(false);
    }
  }, []);

  const createReminder = async (reminder: Omit<ReminderSchedule, 'id'>) => {
    const response = await apiClient.post<ReminderSchedule>('/communications/reminders', reminder);
    if (!response.success || !response.data) throw new Error("Failed to create reminder schedule");
    const newReminder = response.data;
    setReminders(prev => [...prev, newReminder]);
    return newReminder;
  };

  const updateReminder = async (id: string, reminder: Partial<ReminderSchedule>) => {
    await apiClient.put<ReminderSchedule>(`/communications/reminders/${id}`, reminder);
    setReminders(prev => prev.map(r => r.id === id ? { ...r, ...reminder } : r));
  };

  const deleteReminder = async (id: string) => {
    await apiClient.delete<void>(`/communications/reminders/${id}`);
    setReminders(prev => prev.filter(r => r.id !== id));
  };

  // --- Conversations ---
  const fetchConversations = useCallback(async () => {
    setConversationsLoading(true);
    try {
      const response = await apiClient.get<Conversation[]>('/communications/conversations');
      if (response.success && response.data) {
        setConversations(response.data);
      } else {
        setConversations([]);
      }
    } finally {
      setConversationsLoading(false);
    }
  }, []);

  const selectConversation = async (conversationId: string) => {
    setMessagesLoading(true);
    try {
      const response = await apiClient.get<ConversationMessage[]>(`/communications/conversations/${conversationId}/messages`);
      if (response.success && response.data) {
        setConversationMessages(response.data);
      } else {
        setConversationMessages([]);
      }
    } finally {
      setMessagesLoading(false);
    }
  };

  const sendConversationMessage = async (conversationId: string, message: { content: string; senderType: string }) => {
    const messageData = {
      ...message,
      conversationId,
      createdAt: new Date().toISOString(),
    };
    const response = await apiClient.post<ConversationMessage>(`/communications/conversations/${conversationId}/messages`, messageData);
    if (!response.success || !response.data) throw new Error("Failed to send message");
    const newMsg = response.data;
    
    setConversationMessages(prev => [...prev, newMsg as ConversationMessage]);
    
    // Update preview in conversation list
    setConversations(prev => prev.map(c => c.id === conversationId ? { ...c, lastMessagePreview: message.content, lastMessageAt: new Date().toISOString() } : c));
    return newMsg;
  };

  // --- Summary ---
  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const response = await apiClient.get<CommunicationSummary>('/communications/summary');
      if (response.success && response.data) {
        setSummary(response.data);
      } else {
        setSummary(null);
      }
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  return {
    templates,
    templatesLoading,
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    reminders,
    remindersLoading,
    fetchReminders,
    createReminder,
    updateReminder,
    deleteReminder,
    conversations,
    conversationsLoading,
    fetchConversations,
    selectConversation,
    conversationMessages,
    messagesLoading,
    sendConversationMessage,
    summary,
    summaryLoading,
    fetchSummary,
  };
}
