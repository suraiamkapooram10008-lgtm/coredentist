import React from 'react';
import { useNavigate } from 'react-router-dom';
import { format, parseISO, differenceInYears } from 'date-fns';
import { 
  ArrowLeft, 
  Phone, 
  Mail, 
  Calendar, 
  Edit, 
  MoreHorizontal, 
  Stethoscope, 
  CreditCard, 
  UserX, 
  UserCheck 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { PatientRecord } from '@/types/patient';

interface PatientProfileHeaderProps {
  patient: PatientRecord;
  onEdit: () => void;
  onStatusChange: () => void;
  region: string;
}

export const PatientProfileHeader = React.memo(({ patient, onEdit, onStatusChange, region }: PatientProfileHeaderProps) => {
  const navigate = useNavigate();
  const age = differenceInYears(new Date(), parseISO(patient.dateOfBirth));

  return (
    <div className="flex items-start justify-between">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/patients')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="text-2xl font-semibold text-primary">
            {patient.firstName[0]}{patient.lastName[0]}
          </span>
        </div>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">
              {patient.firstName} {patient.lastName}
            </h1>
            <Badge variant={patient.status === 'active' ? 'default' : 'secondary'}>
              {patient.status}
            </Badge>
            {patient.abhaId && (
              <Badge variant="outline" className="border-blue-500 text-blue-600 bg-blue-50/50">
                ABHA: {patient.abhaId}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
            <span>{age} years old</span>
            <span>•</span>
            <span>{format(parseISO(patient.dateOfBirth), 'MMMM d, yyyy')}</span>
            <span>•</span>
            <span className="capitalize">{patient.gender}</span>
            {patient.ssnLastFour && region === 'US' && (
              <>
                <span>•</span>
                <span className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded border border-amber-200 text-amber-700">SSN: ***-**-{patient.ssnLastFour}</span>
              </>
            )}
            {patient.abhaId && region === 'IN' && (
              <>
                <span>•</span>
                <Badge variant="outline" className="border-blue-500 text-blue-600 bg-blue-50/50 hover:bg-blue-100/50">
                  ABHA: {patient.abhaId}
                </Badge>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={() => navigate('/schedule')} className="gap-2">
          <Calendar className="h-4 w-4" />
          Schedule
        </Button>
        <Button onClick={onEdit} className="gap-2">
          <Edit className="h-4 w-4" />
          Edit
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => window.location.href = `tel:${patient.phone}`}>
              <Phone className="h-4 w-4 mr-2" />
              Call Patient
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => window.location.href = `mailto:${patient.email}`}>
              <Mail className="h-4 w-4 mr-2" />
              Send Email
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/chart')}>
              <Stethoscope className="h-4 w-4 mr-2" />
              View Dental Chart
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate('/billing')}>
              <CreditCard className="h-4 w-4 mr-2" />
              View Billing
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              onClick={onStatusChange}
              className={patient.status === 'active' ? 'text-destructive' : 'text-green-600'}
            >
              {patient.status === 'active' ? (
                <>
                  <UserX className="h-4 w-4 mr-2" />
                  Mark Inactive
                </>
              ) : (
                <>
                  <UserCheck className="h-4 w-4 mr-2" />
                  Mark Active
                </>
              )}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
});

PatientProfileHeader.displayName = 'PatientProfileHeader';
