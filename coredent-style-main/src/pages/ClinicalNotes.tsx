import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { clinicalNotesApi, patientsApi } from "@/services/api";
import type { ClinicalNote, Patient } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/auth-context";
import { format } from "date-fns";

export default function ClinicalNotes() {
  const { id: patientId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  const [notes, setNotes] = useState<ClinicalNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [patientLoading, setPatientLoading] = useState(false);
  const [patientError, setPatientError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [noteType, setNoteType] = useState<ClinicalNote["type"]>("general");
  const [content, setContent] = useState("");
  const [subjective, setSubjective] = useState("");
  const [objective, setObjective] = useState("");
  const [assessment, setAssessment] = useState("");
  const [plan, setPlan] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (patientId) {
      loadPatient(patientId);
      loadNotes(patientId);
    } else {
      setPatient(null);
      setNotes([]);
      setError(null);
      setPatientError(null);
    }
  }, [patientId]);

  const loadNotes = async (pid: string) => {
    setLoading(true);
    try {
      const response = await clinicalNotesApi.listByPatient(pid);
      if (response.success && response.data) {
        setNotes(response.data);
      } else {
        setError(response.error?.message || "Failed to load notes");
      }
    } catch (err) {
      setError("An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  const loadPatient = async (pid: string) => {
    setPatientLoading(true);
    setPatientError(null);
    try {
      const response = await patientsApi.getById(pid);
      if (response.success && response.data) {
        setPatient(response.data);
      } else {
        setPatientError(response.error?.message || "Failed to load patient");
      }
    } catch {
      setPatientError("An unexpected error occurred");
    } finally {
      setPatientLoading(false);
    }
  };

  useEffect(() => {
    if (patientId) return;
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timeout = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const response = await patientsApi.list({ search: searchQuery.trim(), limit: 8 });
        if (response.success && response.data) {
          const data = response.data as Patient[] | { data?: Patient[] };
          setSearchResults(Array.isArray(data) ? data : data.data ?? []);
        } else {
          setSearchResults([]);
        }
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery, patientId]);

  const canSave = useMemo(() => {
    if (noteType === "soap") {
      return (
        subjective.trim().length > 0 ||
        objective.trim().length > 0 ||
        assessment.trim().length > 0 ||
        plan.trim().length > 0
      );
    }
    return content.trim().length > 0;
  }, [noteType, subjective, objective, assessment, plan, content]);

  const resetForm = () => {
    setNoteType("general");
    setContent("");
    setSubjective("");
    setObjective("");
    setAssessment("");
    setPlan("");
  };

  const handleCreateNote = async () => {
    if (!patientId || !canSave) return;
    setIsSaving(true);
    try {
      const payload: Omit<ClinicalNote, "id" | "createdAt" | "updatedAt"> = {
        patientId,
        providerId: user?.id || "unknown",
        providerName: user ? `${user.firstName} ${user.lastName}` : "Unknown",
        type: noteType,
        subjective: noteType === "soap" ? subjective.trim() || undefined : undefined,
        objective: noteType === "soap" ? objective.trim() || undefined : undefined,
        assessment: noteType === "soap" ? assessment.trim() || undefined : undefined,
        plan: noteType === "soap" ? plan.trim() || undefined : undefined,
        content: noteType === "soap" ? undefined : content.trim(),
      };
      const response = await clinicalNotesApi.create(payload);
      if (response.success && response.data) {
        setNotes((prev) => [response.data!, ...prev]);
        setIsCreateOpen(false);
        resetForm();
        toast({
          title: "Note created",
          description: "Clinical note saved successfully",
        });
      } else {
        toast({
          title: "Error",
          description: response.error?.message || "Failed to create note",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        title: "Error",
        description: "Failed to create note",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (!patientId) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Clinical Notes</h1>
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="text-muted-foreground">
              Search for a patient to view their clinical notes.
            </div>
            <div className="flex gap-2">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name or email..."
              />
              <Button variant="outline" onClick={() => setSearchQuery("")}>
                Clear
              </Button>
            </div>
            {searchLoading ? (
              <div className="flex justify-center py-6">
                <Spinner size="lg" />
              </div>
            ) : searchResults.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No matching patients.
              </div>
            ) : (
              <div className="space-y-2">
                {searchResults.map((result) => (
                  <Button
                    key={result.id}
                    variant="ghost"
                    className="w-full justify-start"
                    onClick={() => navigate(`/notes/${result.id}`)}
                  >
                    {result.firstName} {result.lastName} · {result.email}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Clinical Notes</h1>
          {patientLoading ? (
            <div className="text-sm text-muted-foreground">Loading patient...</div>
          ) : patient ? (
            <div className="text-sm text-muted-foreground">
              {patient.firstName} {patient.lastName}
            </div>
          ) : patientError ? (
            <div className="text-sm text-destructive">{patientError}</div>
          ) : null}
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>New Note</Button>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Spinner size="lg" />
        </div>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="p-6 text-destructive">{error}</CardContent>
        </Card>
      ) : notes.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            No clinical notes found for this patient.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {notes.map((note) => (
            <Card key={note.id}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg font-medium">
                    {format(new Date(note.createdAt), "PPP p")}
                  </CardTitle>
                  <span className="text-sm text-muted-foreground">
                    by {note.providerName}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                {note.type === "soap" ? (
                  <div className="space-y-3">
                    {note.subjective && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground">Subjective</div>
                        <div className="whitespace-pre-wrap">{note.subjective}</div>
                      </div>
                    )}
                    {note.objective && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground">Objective</div>
                        <div className="whitespace-pre-wrap">{note.objective}</div>
                      </div>
                    )}
                    {note.assessment && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground">Assessment</div>
                        <div className="whitespace-pre-wrap">{note.assessment}</div>
                      </div>
                    )}
                    {note.plan && (
                      <div>
                        <div className="text-xs font-semibold text-muted-foreground">Plan</div>
                        <div className="whitespace-pre-wrap">{note.plan}</div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{note.content}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle>New Clinical Note</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Note Type</Label>
              <Select value={noteType} onValueChange={(v) => setNoteType(v as ClinicalNote["type"])}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">General</SelectItem>
                  <SelectItem value="procedure">Procedure</SelectItem>
                  <SelectItem value="soap">SOAP</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {noteType === "soap" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Subjective</Label>
                  <Textarea
                    value={subjective}
                    onChange={(e) => setSubjective(e.target.value)}
                    rows={4}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Objective</Label>
                  <Textarea
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                    rows={4}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Assessment</Label>
                  <Textarea
                    value={assessment}
                    onChange={(e) => setAssessment(e.target.value)}
                    rows={4}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Plan</Label>
                  <Textarea
                    value={plan}
                    onChange={(e) => setPlan(e.target.value)}
                    rows={4}
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Note</Label>
                <Textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={6}
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateNote} disabled={!canSave || isSaving}>
              {isSaving ? "Saving..." : "Save Note"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
