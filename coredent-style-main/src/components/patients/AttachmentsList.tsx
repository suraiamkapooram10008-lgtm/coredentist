// ============================================
// Attachments List Component
// Display and manage patient file attachments
// ============================================

import { useState, useRef } from 'react';
import { format, parseISO } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { 
  Upload, 
  File, 
  FileText, 
  Image, 
  Download, 
  Trash2, 
  MoreHorizontal,
  FileCheck,
  Send,
  CloudOff,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { patientApi } from '@/services/patientApi';
import type { PatientAttachment } from '@/types/patient';
import { attachmentCategoryConfig } from '@/types/patient';

interface AttachmentsListProps {
  attachments: PatientAttachment[];
  patientId: string;
  onUpload: () => void;
  onDelete: () => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(type: string) {
  if (type.startsWith('image/')) return Image;
  if (type === 'application/pdf') return FileText;
  return File;
}

export function AttachmentsList({
  attachments,
  patientId,
  onUpload,
  onDelete,
}: AttachmentsListProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedCategory, setSelectedCategory] = useState<PatientAttachment['category']>('other');
  const [isUploading, setIsUploading] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await patientApi.uploadAttachment(patientId, file, selectedCategory);
      onUpload();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await patientApi.deleteAttachment(patientId, deleteId);
      onDelete();
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setDeleteId(null);
    }
  };

  const filteredAttachments = filterCategory === 'all' 
    ? attachments 
    : attachments.filter(a => a.category === filterCategory);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Files & Attachments</CardTitle>
        <div className="flex items-center gap-2">
          <Select value={filterCategory} onValueChange={setFilterCategory}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Files</SelectItem>
              {Object.entries(attachmentCategoryConfig).map(([key, config]) => (
                <SelectItem key={key} value={key}>
                  {config.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <div className="flex items-center gap-2">
            <Select
              value={selectedCategory}
              onValueChange={(value) => setSelectedCategory(value as PatientAttachment['category'])}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(attachmentCategoryConfig).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            />
            <Button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="gap-2"
            >
              <Upload className="h-4 w-4" />
              {isUploading ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Cloud storage notice */}
        <div className="mb-4 p-3 rounded-lg bg-muted/50 border border-dashed flex items-center gap-3">
          <CloudOff className="h-5 w-5 text-muted-foreground" />
          <div className="text-sm text-muted-foreground">
            <p>File storage requires Lovable Cloud to be enabled.</p>
            <p className="text-xs">Enable Cloud for persistent file uploads.</p>
          </div>
        </div>

        {filteredAttachments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <File className="h-12 w-12 mb-2 opacity-30" />
            <p>No files attached</p>
            <p className="text-sm">Upload files to attach them to this patient</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredAttachments.map((attachment) => {
              const Icon = getFileIcon(attachment.type);
              const categoryConfig = attachmentCategoryConfig[attachment.category];

              return (
                <div
                  key={attachment.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="font-medium text-sm">{attachment.name}</div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline" className="text-xs">
                          {categoryConfig.label}
                        </Badge>
                        <span>{formatFileSize(attachment.size)}</span>
                        <span>•</span>
                        <span>{format(parseISO(attachment.uploadedAt), 'MMM d, yyyy')}</span>
                      </div>
                    </div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem asChild>
                        <a href={attachment.url} download={attachment.name}>
                          <Download className="h-4 w-4 mr-2" />
                          Download
                        </a>
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => setDeleteId(attachment.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Attachment?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The file will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
