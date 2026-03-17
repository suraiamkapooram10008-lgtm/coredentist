// ============================================
// Patient Search Dialog
// Quick patient search for scheduling
// ============================================

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Search, User, Phone, Mail, Calendar, Plus } from 'lucide-react';
import type { PatientSearchResult } from '@/types/scheduling';
import { schedulingApi } from '@/services/schedulingApi';
import { format } from 'date-fns';

interface PatientSearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectPatient: (patient: PatientSearchResult) => void;
}

export function PatientSearchDialog({
  open,
  onOpenChange,
  onSelectPatient,
}: PatientSearchDialogProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PatientSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setQuery('');
      setResults([]);
    }
  }, [open]);

  useEffect(() => {
    const searchPatients = async () => {
      if (query.length >= 2) {
        setIsLoading(true);
        try {
          const data = await schedulingApi.searchPatients(query);
          setResults(data);
        } catch (error) {
          console.error('Patient search failed:', error);
        } finally {
          setIsLoading(false);
        }
      } else {
        setResults([]);
      }
    };

    const debounce = setTimeout(searchPatients, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  const handleSelect = (patient: PatientSearchResult) => {
    onSelectPatient(patient);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Find Patient</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, phone, or email..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
              autoFocus
            />
            {isLoading && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            )}
          </div>

          {/* Results */}
          <ScrollArea className="h-[300px]">
            {results.length > 0 ? (
              <div className="space-y-2">
                {results.map((patient) => (
                  <div
                    key={patient.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => handleSelect(patient)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="font-medium">{patient.name}</div>
                        <div className="text-sm text-muted-foreground flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {patient.phone}
                          </span>
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {patient.email}
                          </span>
                        </div>
                        {patient.lastVisit && (
                          <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                            <Calendar className="h-3 w-3" />
                            Last visit: {format(new Date(patient.lastVisit), 'MMM d, yyyy')}
                          </div>
                        )}
                      </div>
                    </div>
                    <Button size="sm" variant="ghost">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : query.length >= 2 && !isLoading ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                <User className="h-12 w-12 mb-2 opacity-30" />
                <p>No patients found</p>
                <p className="text-sm">Try a different search term</p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                <Search className="h-12 w-12 mb-2 opacity-30" />
                <p>Search for a patient</p>
                <p className="text-sm">Enter at least 2 characters</p>
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}
