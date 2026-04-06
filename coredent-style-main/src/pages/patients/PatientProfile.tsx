// ============================================
// CoreDent PMS - Patient Profile Page
// Comprehensive view of patient records
// ============================================

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/auth-context';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';

// Components & Hooks
import { patientsApi } from '@/services/api';
import { useApiRequest } from '@/hooks/useApiRequest';
import { PatientProfileHeader } from '@/components/patients/PatientProfileHeader';
import { PatientQuickStats } from '@/components/patients/PatientQuickStats';
import { PatientOverviewTab } from '@/components/patients/PatientOverviewTab';
import { PatientMedicalTab } from '@/components/patients/PatientMedicalTab';
import { PatientDialog } from '@/components/patients/PatientDialog';
import { AddNoteDialog } from '@/components/patients/AddNoteDialog';
import { AppointmentHistory } from '@/components/patients/AppointmentHistory';
import { AttachmentsList } from '@/components/patients/AttachmentsList';
import type { PatientRecord } from '@/types/patient';

export default function PatientProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Dialog States
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isAddNoteDialogOpen, setIsAddNoteDialogOpen] = useState(false);

  // Region Config (US vs INDIA)
  const region = user?.practiceCountry || 'US';

  // Memoized Fetcher
  const fetchPatient = useCallback(() => patientsApi.getById(id!) as Promise<PatientRecord>, [id]);

  // API Hooks
  const {
    data: patient,
    isLoading,
    error,
    execute: loadPatient,
    setData: setPatient
  } = useApiRequest<PatientRecord>(fetchPatient, {
    errorMessage: 'Failed to load patient profile'
  });

  const { execute: updateStatus } = useApiRequest(
    (status: 'active' | 'inactive') => patientsApi.update(id!, { status }),
    {
      successMessage: 'Patient status updated',
      onSuccess: (updated) => setPatient(updated as PatientRecord)
    }
  );

  useEffect(() => {
    if (id) {
      loadPatient();
    } else {
      navigate('/patients');
    }
  }, [id, loadPatient, navigate]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-16 w-16 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error || 'Patient not found. Re-directing...'}
        </AlertDescription>
      </Alert>
    );
  }

  const handleStatusChange = () => {
    const newStatus = patient.status === 'active' ? 'inactive' : 'active';
    updateStatus(newStatus);
  };

  return (
    <div className="space-y-6">
      <PatientProfileHeader 
        patient={patient} 
        onEdit={() => setIsEditDialogOpen(true)} 
        onStatusChange={handleStatusChange} 
        region={region}
      />

      {patient.medicalHistory?.allergies?.length > 0 && (
        <Alert variant="destructive" className="bg-red-50 border-red-200">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800 font-bold">Medical Alert: Allergies</AlertTitle>
          <AlertDescription className="text-red-700">
            {patient.medicalHistory.allergies.join(', ')}
          </AlertDescription>
        </Alert>
      )}

      <PatientQuickStats 
        stats={patient.appointmentStats} 
        notesCount={patient.notes.length} 
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
          <TabsTrigger value="overview" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Overview</TabsTrigger>
          <TabsTrigger value="medical" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Medical/Dental</TabsTrigger>
          <TabsTrigger value="appointments" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Appointments</TabsTrigger>
          <TabsTrigger value="files" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Files & Images</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <PatientOverviewTab 
            patient={patient} 
            onAddNote={() => setIsAddNoteDialogOpen(true)} 
            region={region}
          />
        </TabsContent>

        <TabsContent value="medical" className="mt-6">
          <PatientMedicalTab 
            medicalHistory={patient.medicalHistory} 
            dentalHistory={patient.dentalHistory} 
          />
        </TabsContent>

        <TabsContent value="appointments" className="mt-6">
          <AppointmentHistory appointments={patient.appointments} />
        </TabsContent>

        <TabsContent value="files" className="mt-6">
          <AttachmentsList 
            patientId={patient.id}
            attachments={patient.attachments} 
            onUpload={() => loadPatient()}
            onDelete={() => loadPatient()}
          />
        </TabsContent>
      </Tabs>

      <PatientDialog 
        open={isEditDialogOpen} 
        onOpenChange={setIsEditDialogOpen} 
        patient={patient}
        onSave={() => loadPatient()}
        region={region}
      />

      <AddNoteDialog 
        open={isAddNoteDialogOpen} 
        onOpenChange={setIsAddNoteDialogOpen} 
        patientId={patient.id}
        onSave={() => loadPatient()}
      />
    </div>
  );
}
