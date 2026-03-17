import React from 'react';
import { format, parseISO } from 'date-fns';
import { Heart, AlertTriangle, Pill, Stethoscope } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import type { PatientRecord } from '@/types/patient';

interface PatientMedicalTabProps {
  medicalHistory: PatientRecord['medicalHistory'];
  dentalHistory: PatientRecord['dentalHistory'];
}

export const PatientMedicalTab = React.memo(({ medicalHistory, dentalHistory }: PatientMedicalTabProps) => {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Heart className="h-5 w-5 text-red-500" />
            Medical Conditions
          </CardTitle>
        </CardHeader>
        <CardContent>
          {medicalHistory.conditions.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {medicalHistory.conditions.map((condition, i) => (
                <Badge key={i} variant="secondary">{condition}</Badge>
              ))}
            </div>
          ) : (
            <span className="text-muted-foreground">None reported</span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Allergies
          </CardTitle>
        </CardHeader>
        <CardContent>
          {medicalHistory.allergies.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {medicalHistory.allergies.map((allergy, i) => (
                <Badge key={i} variant="destructive">{allergy}</Badge>
              ))}
            </div>
          ) : (
            <span className="text-muted-foreground">No known allergies</span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Pill className="h-5 w-5 text-blue-500" />
            Current Medications
          </CardTitle>
        </CardHeader>
        <CardContent>
          {medicalHistory.medications.length > 0 ? (
            <ul className="space-y-2">
              {medicalHistory.medications.map((med, i) => (
                <li key={i} className="text-sm">{med}</li>
              ))}
            </ul>
          ) : (
            <span className="text-muted-foreground">No medications</span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-primary" />
            Dental History
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground">Last Cleaning:</span>
              <span className="ml-2">
                {dentalHistory.lastCleaning 
                  ? format(parseISO(dentalHistory.lastCleaning), 'MMM d, yyyy')
                  : 'Unknown'
                }
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Last X-Rays:</span>
              <span className="ml-2">
                {dentalHistory.lastXrays 
                  ? format(parseISO(dentalHistory.lastXrays), 'MMM d, yyyy')
                  : 'Unknown'
                }
              </span>
            </div>
          </div>
          <Separator />
          <div className="flex flex-wrap gap-2">
            {dentalHistory.gumDiseaseHistory && <Badge variant="outline">Gum Disease History</Badge>}
            {dentalHistory.toothSensitivity && <Badge variant="outline">Tooth Sensitivity</Badge>}
            {dentalHistory.grindsClenches && <Badge variant="outline">Grinds/Clenches</Badge>}
            {dentalHistory.hasImplants && <Badge variant="outline">Has Implants</Badge>}
            {dentalHistory.missingTeeth.length > 0 && (
              <Badge variant="outline">
                Missing Teeth: {dentalHistory.missingTeeth.join(', ')}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
});

PatientMedicalTab.displayName = 'PatientMedicalTab';
