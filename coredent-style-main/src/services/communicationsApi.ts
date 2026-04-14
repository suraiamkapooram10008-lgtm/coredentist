/**
 * Communications API Service
 * Patient messaging, SMS/email reminders, two-way messaging
 */

import { apiClient } from './api';

// Types
export interface MessageTemplate {
  id: string;
  practiceId: string;
  name: string;
  messageType: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  subject?: string;
  content: string;
  category?: string;
  variables?: string[];
  isActive: boolean;
  isDefault: boolean;
  timesUsed: number;
  createdAt: string;
  updatedAt: string;
}

export interface MessageTemplateCreate {
  name: string;
  messageType: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  subject?: string;
  content: string;
  category?: string;
  variables?: string[];
  isActive?: boolean;
  isDefault?: boolean;
}

export interface MessageTemplateUpdate {
  name?: string;
  subject?: string;
  content?: string;
  category?: string;
  variables?: string[];
  isActive?: boolean;
  isDefault?: boolean;
}

export interface PatientMessage {
  id: string;
  practiceId: string;
  patientId: string;
  userId?: string;
  templateId?: string;
  appointmentId?: string;
  parentMessageId?: string;
  messageType: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  direction: 'outbound' | 'inbound';
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'read';
  subject?: string;
  content: string;
  recipientPhone?: string;
  recipientEmail?: string;
  fromName?: string;
  fromEmail?: string;
  externalId?: string;
  providerResponse?: string;
  scheduledAt?: string;
  sentAt?: string;
  deliveredAt?: string;
  readAt?: string;
  errorMessage?: string;
  errorCode?: string;
  attachments?: string[];
  cost?: string;
  createdAt: string;
  updatedAt: string;
}

export interface PatientMessageCreate {
  patientId: string;
  messageType: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  direction: 'outbound' | 'inbound';
  content: string;
  subject?: string;
  recipientPhone?: string;
  recipientEmail?: string;
  fromName?: string;
  fromEmail?: string;
  scheduledAt?: string;
  templateId?: string;
  appointmentId?: string;
  parentMessageId?: string;
  attachments?: string[];
}

export interface ReminderSchedule {
  id: string;
  practiceId: string;
  templateId: string;
  appointmentTypeId?: string;
  name: string;
  reminderType: 'appointment' | 'recall' | 'treatment' | 'payment' | 'insurance' | 'custom';
  daysBefore: number;
  daysAfter: number;
  hoursBefore: number;
  minutesBefore: number;
  specificTime?: string;
  messageType: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  isActive: boolean;
  sendOnWeekends: boolean;
  maxReminders: number;
  patientTypes?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ReminderScheduleCreate {
  name: string;
  reminderType: 'appointment' | 'recall' | 'treatment' | 'payment' | 'insurance' | 'custom';
  daysBefore?: number;
  daysAfter?: number;
  hoursBefore?: number;
  minutesBefore?: number;
  specificTime?: string;
  messageType: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  isActive?: boolean;
  sendOnWeekends?: boolean;
  maxReminders?: number;
  patientTypes?: string[];
  templateId: string;
  appointmentTypeId?: string;
}

export interface ReminderScheduleUpdate {
  name?: string;
  reminderType?: 'appointment' | 'recall' | 'treatment' | 'payment' | 'insurance' | 'custom';
  daysBefore?: number;
  daysAfter?: number;
  hoursBefore?: number;
  minutesBefore?: number;
  specificTime?: string;
  messageType?: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  isActive?: boolean;
  sendOnWeekends?: boolean;
  maxReminders?: number;
  patientTypes?: string[];
}

export interface Conversation {
  id: string;
  practiceId: string;
  patientId: string;
  assignedUserId?: string;
  channel: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  subject?: string;
  status: string;
  lastMessageAt?: string;
  lastMessagePreview?: string;
  unreadCount: number;
  autoResponderEnabled: boolean;
  autoResponseTemplateId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationCreate {
  patientId: string;
  channel: 'sms' | 'email' | 'voice' | 'push' | 'in_app';
  subject?: string;
  status?: string;
  autoResponderEnabled?: boolean;
  autoResponseTemplateId?: string;
}

export interface ConversationMessage {
  id: string;
  conversationId: string;
  senderId?: string;
  senderType: string;
  content: string;
  attachments?: string[];
  isRead: boolean;
  readAt?: string;
  externalId?: string;
  createdAt: string;
}

export interface ConversationMessageCreate {
  conversationId: string;
  senderType: string;
  content: string;
  senderId?: string;
  attachments?: string[];
}

export interface MessageStats {
  totalSent: number;
  totalDelivered: number;
  totalFailed: number;
  deliveryRate: number;
  totalCost: string;
}

export interface ReminderStats {
  totalScheduled: number;
  totalSent: number;
  totalDelivered: number;
  pending: number;
  failed: number;
}

export interface CommunicationSummary {
  messages: MessageStats;
  reminders: ReminderStats;
  activeConversations: number;
  unreadMessages: number;
}

// API Service
export const communicationsApi = {
  // Templates
  templates: {
    list: (params?: { category?: string; isActive?: boolean; messageType?: string }) =>
      apiClient.get<MessageTemplate[]>('/communications/templates', params as Record<string, unknown>),
    
    get: (templateId: string) =>
      apiClient.get<MessageTemplate>(`/communications/templates/${templateId}`),
    
    create: (template: MessageTemplateCreate) =>
      apiClient.post<MessageTemplate>('/communications/templates', template),
    
    update: (templateId: string, template: MessageTemplateUpdate) =>
      apiClient.put<MessageTemplate>(`/communications/templates/${templateId}`, template),
    
    delete: (templateId: string) =>
      apiClient.delete<void>(`/communications/templates/${templateId}`),
  },

  // Messages
  messages: {
    list: (params?: {
      patientId?: string;
      messageType?: string;
      status?: string;
      direction?: string;
      dateFrom?: string;
      dateTo?: string;
    }) =>
      apiClient.get<PatientMessage[]>('/communications/messages', params as Record<string, unknown>),
    
    get: (messageId: string) =>
      apiClient.get<PatientMessage>(`/communications/messages/${messageId}`),
    
    send: (message: PatientMessageCreate) =>
      apiClient.post<PatientMessage>('/communications/messages', message),
    
    update: (messageId: string, message: Partial<PatientMessageCreate>) =>
      apiClient.put<PatientMessage>(`/communications/messages/${messageId}`, message),
  },

  // Reminders
  reminders: {
    list: (params?: { isActive?: boolean; reminderType?: string }) =>
      apiClient.get<ReminderSchedule[]>('/communications/reminders', params as Record<string, unknown>),
    
    get: (reminderId: string) =>
      apiClient.get<ReminderSchedule>(`/communications/reminders/${reminderId}`),
    
    create: (reminder: ReminderScheduleCreate) =>
      apiClient.post<ReminderSchedule>('/communications/reminders', reminder),
    
    update: (reminderId: string, reminder: ReminderScheduleUpdate) =>
      apiClient.put<ReminderSchedule>(`/communications/reminders/${reminderId}`, reminder),
    
    delete: (reminderId: string) =>
      apiClient.delete<void>(`/communications/reminders/${reminderId}`),
  },

  // Conversations
  conversations: {
    list: (params?: { status?: string; patientId?: string }) =>
      apiClient.get<Conversation[]>('/communications/conversations', params as Record<string, unknown>),
    
    get: (conversationId: string) =>
      apiClient.get<Conversation>(`/communications/conversations/${conversationId}`),
    
    create: (conversation: ConversationCreate) =>
      apiClient.post<Conversation>('/communications/conversations', conversation),
    
    update: (conversationId: string, conversation: Partial<ConversationCreate>) =>
      apiClient.put<Conversation>(`/communications/conversations/${conversationId}`, conversation),
    
    getMessages: (conversationId: string, skip?: number, limit?: number) =>
      apiClient.get<ConversationMessage[]>(
        `/communications/conversations/${conversationId}/messages`,
        skip !== undefined ? { skip, limit } : undefined
      ),
    
    sendMessage: (conversationId: string, message: ConversationMessageCreate) =>
      apiClient.post<ConversationMessage>(
        `/communications/conversations/${conversationId}/messages`,
        message
      ),
  },

  // Settings & Stats
  getSummary: () =>
    apiClient.get<CommunicationSummary>('/communications/settings'),
};