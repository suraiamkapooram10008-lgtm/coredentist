// ============================================
// CoreDent PMS - Imaging API Service
// API calls for imaging management
// ============================================

import type {
  PatientImage,
  ImageSeries,
  ImageTemplate,
  ImagingSummary,
  ImageType,
  ImageCategory,
  ImageAnnotation,
} from '@/types/imaging';
import { apiClient } from './api';

export const imagingApi = {
  // ============================================
  // Patient Images
  // ============================================

  async getImages(filters?: {
    patientId?: string;
    seriesId?: string;
    imageType?: ImageType;
    category?: ImageCategory;
    startDate?: string;
    endDate?: string;
  }): Promise<PatientImage[]> {
    const response = await apiClient.get<PatientImage[]>('/imaging/images', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  async getImage(imageId: string): Promise<PatientImage | null> {
    const response = await apiClient.get<PatientImage>(`/imaging/images/${imageId}`);
    return response.success ? response.data ?? null : null;
  },

  async uploadImage(data: {
    patientId: string;
    seriesId?: string;
    imageType: ImageType;
    category: ImageCategory;
    title: string;
    description?: string;
    toothNumber?: string;
    captureDate: string;
    file: File;
    tags?: string[];
  }): Promise<PatientImage> {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('patientId', data.patientId);
    if (data.seriesId) formData.append('seriesId', data.seriesId);
    formData.append('imageType', data.imageType);
    formData.append('category', data.category);
    formData.append('title', data.title);
    if (data.description) formData.append('description', data.description);
    if (data.toothNumber) formData.append('toothNumber', data.toothNumber);
    formData.append('captureDate', data.captureDate);
    if (data.tags) formData.append('tags', JSON.stringify(data.tags));

    const response = await apiClient.post<PatientImage>('/imaging/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to upload image');
  },

  async updateImage(imageId: string, data: Partial<PatientImage>): Promise<PatientImage> {
    const response = await apiClient.put<PatientImage>(`/imaging/images/${imageId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update image');
  },

  async deleteImage(imageId: string): Promise<void> {
    await apiClient.delete<void>(`/imaging/images/${imageId}`);
  },

  async addAnnotation(imageId: string, annotation: Omit<ImageAnnotation, 'id'>): Promise<PatientImage> {
    const response = await apiClient.post<PatientImage>(`/imaging/images/${imageId}/annotations`, annotation);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to add annotation');
  },

  async deleteAnnotation(imageId: string, annotationId: string): Promise<PatientImage> {
    const response = await apiClient.delete<PatientImage>(`/imaging/images/${imageId}/annotations/${annotationId}`);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to delete annotation');
  },

  // ============================================
  // Image Series
  // ============================================

  async getSeries(filters?: { patientId?: string }): Promise<ImageSeries[]> {
    const response = await apiClient.get<ImageSeries[]>('/imaging/series', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  async getSeriesById(seriesId: string): Promise<ImageSeries | null> {
    const response = await apiClient.get<ImageSeries>(`/imaging/series/${seriesId}`);
    return response.success ? response.data ?? null : null;
  },

  async createSeries(data: {
    patientId: string;
    name: string;
    description?: string;
    seriesDate: string;
  }): Promise<ImageSeries> {
    const response = await apiClient.post<ImageSeries>('/imaging/series', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create series');
  },

  async updateSeries(seriesId: string, data: Partial<ImageSeries>): Promise<ImageSeries> {
    const response = await apiClient.put<ImageSeries>(`/imaging/series/${seriesId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update series');
  },

  async deleteSeries(seriesId: string): Promise<void> {
    await apiClient.delete<void>(`/imaging/series/${seriesId}`);
  },

  // ============================================
  // Image Templates
  // ============================================

  async getTemplates(filters?: { isActive?: boolean }): Promise<ImageTemplate[]> {
    const response = await apiClient.get<ImageTemplate[]>('/imaging/templates', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  async getTemplate(templateId: string): Promise<ImageTemplate | null> {
    const response = await apiClient.get<ImageTemplate>(`/imaging/templates/${templateId}`);
    return response.success ? response.data ?? null : null;
  },

  async createTemplate(data: Omit<ImageTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<ImageTemplate> {
    const response = await apiClient.post<ImageTemplate>('/imaging/templates', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create template');
  },

  async updateTemplate(templateId: string, data: Partial<ImageTemplate>): Promise<ImageTemplate> {
    const response = await apiClient.put<ImageTemplate>(`/imaging/templates/${templateId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update template');
  },

  async deleteTemplate(templateId: string): Promise<void> {
    await apiClient.delete<void>(`/imaging/templates/${templateId}`);
  },

  // ============================================
  // Summary & Reports
  // ============================================

  async getSummary(): Promise<ImagingSummary> {
    const response = await apiClient.get<ImagingSummary>('/imaging/summary');
    if (response.success && response.data) {
      return response.data;
    }
    return {
      totalImages: 0,
      imagesByType: { xray: 0, photo: 0, scan: 0, other: 0 },
      imagesByCategory: {
        periapical: 0,
        bitewing: 0,
        panoramic: 0,
        cephalometric: 0,
        cbct: 0,
        intraoral: 0,
        extraoral: 0,
        other: 0,
      },
      totalSeries: 0,
      storageUsed: 0,
      recentImages: [],
    };
  },

  // ============================================
  // Utility Functions
  // ============================================

  getImageUrl(image: PatientImage): string {
    return image.fileUrl;
  },

  getThumbnailUrl(image: PatientImage): string {
    return image.thumbnailUrl || image.fileUrl;
  },

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  },
};
