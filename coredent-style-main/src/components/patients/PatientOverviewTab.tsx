import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, Mail, MapPin, User, Plus, FileText, ShieldCheck, ShieldAlert } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { NotesTimeline } from '@/components/patients/NotesTimeline';
import { format, parseISO } from 'date-fns';
import type { PatientRecord } from '@/types/patient';

interface PatientOverviewTabProps {
  patient: PatientRecord;
  onAddNote: () => void;
  region: string;
}

export const PatientOverviewTab = React.memo(({ patient, onAddNote, region }: PatientOverviewTabProps) => {
  const navigate = useNavigate();

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Contact Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Phone className="h-4 w-4 text-muted-foreground" />
            <span>{patient.phone}</span>
          </div>
          <div className="flex items-center gap-3">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span>{patient.email}</span>
          </div>
          <div className="flex items-start gap-3">
            <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div>
              <div>{patient.address.street}</div>
              <div>{patient.address.city}, {patient.address.state} {patient.address.zipCode}</div>
              <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider font-semibold">
                {region === 'IN' ? 'Pincode' : 'Zip Code'}: {patient.address.zipCode}
              </div>
            </div>
          </div>
          
          <div className="border-t pt-4 mt-4">
            {patient.consentRecordedAt ? (
              <div className="flex items-center gap-3 text-green-600 text-sm font-medium">
                <ShieldCheck className="h-4 w-4" />
                <span>Privacy Data Consent: Recorded ({format(parseISO(patient.consentRecordedAt), 'MMM d, yyyy')})</span>
              </div>
            ) : (
              <div className="flex items-center gap-3 text-amber-600 text-sm font-medium">
                <ShieldAlert className="h-4 w-4" />
                <span>Privacy Data Consent: Action Required (DPDP/HIPAA)</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Emergency Contact */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Emergency Contact</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <User className="h-4 w-4 text-muted-foreground" />
            <span>{patient.emergencyContact.name}</span>
            <Badge variant="secondary" className="text-xs">
              {patient.emergencyContact.relationship}
            </Badge>
          </div>
          <div className="flex items-center gap-3">
            <Phone className="h-4 w-4 text-muted-foreground" />
            <span>{patient.emergencyContact.phone}</span>
          </div>
        </CardContent>
      </Card>

      {/* Insurance Information */}
      {patient.insuranceInfo && (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Insurance Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <div className="text-sm text-muted-foreground">Provider</div>
                <div className="font-medium">{patient.insuranceInfo.provider}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Policy Number</div>
                <div className="font-medium">{patient.insuranceInfo.policyNumber}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Group Number</div>
                <div className="font-medium">{patient.insuranceInfo.groupNumber}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Subscriber</div>
                <div className="font-medium">{patient.insuranceInfo.subscriberName}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Notes Preview */}
      <Card className="lg:col-span-2">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Recent Notes</CardTitle>
          <Button variant="outline" size="sm" onClick={onAddNote}>
            <Plus className="h-4 w-4 mr-1" />
            Add Note
          </Button>
        </CardHeader>
        <CardContent>
          {patient.notes.length > 0 ? (
            <NotesTimeline notes={patient.notes.slice(0, 3)} compact />
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <FileText className="h-12 w-12 mx-auto mb-2 opacity-30" />
              <p>No notes yet</p>
            </div>
          )}
          {patient.notes.length > 3 && (
            <Button 
              variant="ghost" 
              className="w-full mt-4"
              onClick={() => navigate(`/notes/${patient.id}`)}
            >
              View All Notes
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
});

PatientOverviewTab.displayName = 'PatientOverviewTab';
