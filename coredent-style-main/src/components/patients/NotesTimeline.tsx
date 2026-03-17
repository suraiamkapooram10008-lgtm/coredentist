// ============================================
// Notes Timeline Component
// Displays patient notes in chronological order
// ============================================

import { format, parseISO } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  MoreHorizontal, 
  Trash2, 
  Pin, 
  FileText,
  MessageSquare,
  Stethoscope,
  CreditCard,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PatientNote } from '@/types/patient';
import { noteTypeConfig } from '@/types/patient';

interface NotesTimelineProps {
  notes: PatientNote[];
  compact?: boolean;
  onDelete?: (noteId: string) => void;
  onPin?: (noteId: string) => void;
}

const noteTypeIcons: Record<PatientNote['type'], React.ComponentType<{ className?: string }>> = {
  general: FileText,
  clinical: Stethoscope,
  billing: CreditCard,
  communication: MessageSquare,
  alert: AlertTriangle,
};

export function NotesTimeline({ notes, compact, onDelete, onPin }: NotesTimelineProps) {
  if (notes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mb-2 opacity-30" />
        <p>No notes yet</p>
      </div>
    );
  }

  // Sort by date, pinned first
  const sortedNotes = [...notes].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  return (
    <div className="space-y-4">
      {sortedNotes.map((note, index) => {
        const config = noteTypeConfig[note.type];
        const Icon = noteTypeIcons[note.type];

        return (
          <div
            key={note.id}
            className={cn(
              "relative pl-8 pb-4",
              index !== sortedNotes.length - 1 && "border-l-2 border-muted ml-3"
            )}
          >
            {/* Timeline dot */}
            <div 
              className="absolute left-0 -translate-x-1/2 w-6 h-6 rounded-full flex items-center justify-center"
              style={{ backgroundColor: `${config.color}20` }}
            >
              <Icon className={cn("h-3 w-3")} />
            </div>

            {/* Note content */}
            <div className={cn(
              "rounded-lg border p-4",
              note.isPinned && "border-primary/50 bg-primary/5"
            )}>
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge className={config.bgClass}>
                    {config.label}
                  </Badge>
                  {note.isPinned && (
                    <Badge variant="outline" className="gap-1">
                      <Pin className="h-3 w-3" />
                      Pinned
                    </Badge>
                  )}
                  {note.isAlert && (
                    <Badge variant="destructive">Alert</Badge>
                  )}
                </div>
                
                {!compact && (onDelete || onPin) && (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {onPin && (
                        <DropdownMenuItem onClick={() => onPin(note.id)}>
                          <Pin className="h-4 w-4 mr-2" />
                          {note.isPinned ? 'Unpin' : 'Pin to Top'}
                        </DropdownMenuItem>
                      )}
                      {onDelete && (
                        <DropdownMenuItem 
                          onClick={() => onDelete(note.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </div>

              {/* Content */}
              <p className={cn(
                "text-sm",
                compact && "line-clamp-2"
              )}>
                {note.content}
              </p>

              {/* Footer */}
              <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
                <span>{note.createdByName}</span>
                <span>•</span>
                <span>{format(parseISO(note.createdAt), 'MMM d, yyyy h:mm a')}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
