// ============================================
// CoreDent PMS - Confirmation Dialog
// Reusable confirmation prompt with variants
// ============================================

import React, { useState } from 'react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, AlertTriangle, Trash2, UserX, Ban } from 'lucide-react';

type ConfirmationType = 'danger' | 'warning' | 'deactivate' | 'delete';

interface ConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  type?: ConfirmationType;
  confirmText?: string;
  cancelText?: string;
  requireTypedConfirmation?: string;
  onConfirm: () => Promise<void> | void;
  isLoading?: boolean;
}

const typeConfig: Record<ConfirmationType, { icon: React.ElementType; buttonClass: string }> = {
  danger: {
    icon: AlertTriangle,
    buttonClass: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  },
  warning: {
    icon: AlertTriangle,
    buttonClass: 'bg-yellow-600 text-white hover:bg-yellow-700',
  },
  deactivate: {
    icon: UserX,
    buttonClass: 'bg-orange-600 text-white hover:bg-orange-700',
  },
  delete: {
    icon: Trash2,
    buttonClass: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  },
};

export function ConfirmationDialog({
  open,
  onOpenChange,
  title,
  description,
  type = 'danger',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  requireTypedConfirmation,
  onConfirm,
  isLoading = false,
}: ConfirmationDialogProps) {
  const [typedValue, setTypedValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const config = typeConfig[type];
  const Icon = config.icon;

  const canConfirm = requireTypedConfirmation
    ? typedValue.toLowerCase() === requireTypedConfirmation.toLowerCase()
    : true;

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true);
      await onConfirm();
      onOpenChange(false);
      setTypedValue('');
    } catch (error) {
      // Error handling should be done by the parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setTypedValue('');
    }
    onOpenChange(open);
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
              type === 'warning' ? 'bg-yellow-100 dark:bg-yellow-900/30' : 'bg-destructive/10'
            }`}>
              <Icon className={`h-5 w-5 ${
                type === 'warning' ? 'text-yellow-600 dark:text-yellow-500' : 'text-destructive'
              }`} />
            </div>
            <AlertDialogTitle>{title}</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="pt-2">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {requireTypedConfirmation && (
          <div className="space-y-2 py-4">
            <Label htmlFor="confirmation">
              Type <span className="font-mono font-bold">{requireTypedConfirmation}</span> to confirm
            </Label>
            <Input
              id="confirmation"
              value={typedValue}
              onChange={e => setTypedValue(e.target.value)}
              placeholder={requireTypedConfirmation}
              autoComplete="off"
            />
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isSubmitting || isLoading}>
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={!canConfirm || isSubmitting || isLoading}
            className={config.buttonClass}
          >
            {(isSubmitting || isLoading) && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
