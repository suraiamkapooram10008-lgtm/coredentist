// ============================================
// Add Note Dialog Component
// Add notes to patient records
// ============================================

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { patientApi } from '@/services/patientApi';
import type { PatientNote } from '@/types/patient';
import { noteTypeConfig } from '@/types/patient';

interface AddNoteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patientId: string;
  onSave: () => void;
}

export function AddNoteDialog({
  open,
  onOpenChange,
  patientId,
  onSave,
}: AddNoteDialogProps) {
  const [type, setType] = useState<PatientNote['type']>('general');
  const [content, setContent] = useState('');
  const [isAlert, setIsAlert] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (!content.trim()) return;
    
    setIsSaving(true);
    try {
      await patientApi.addNote(patientId, {
        type,
        content: content.trim(),
        createdBy: '1', // Would come from auth context
        createdByName: 'Current User',
        isAlert,
        isPinned,
      });
      
      // Reset form
      setType('general');
      setContent('');
      setIsAlert(false);
      setIsPinned(false);
      
      onSave();
    } catch (error) {
      console.error('Failed to add note:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Note</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Note Type</Label>
            <Select value={type} onValueChange={(v) => setType(v as PatientNote['type'])}>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(noteTypeConfig).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: config.color }}
                      />
                      {config.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Note Content</Label>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your note here..."
              rows={5}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch
                id="isAlert"
                checked={isAlert}
                onCheckedChange={setIsAlert}
              />
              <Label htmlFor="isAlert" className="cursor-pointer">
                Mark as Alert
              </Label>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch
                id="isPinned"
                checked={isPinned}
                onCheckedChange={setIsPinned}
              />
              <Label htmlFor="isPinned" className="cursor-pointer">
                Pin to Top
              </Label>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!content.trim() || isSaving}>
            {isSaving ? 'Saving...' : 'Add Note'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
