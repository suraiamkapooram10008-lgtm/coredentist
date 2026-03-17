// ============================================
// Patient List Page
// Main patient directory with search and filters
// ============================================

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Search, 
  Plus, 
  Filter, 
  MoreHorizontal,
  Phone,
  Mail,
  Calendar,
  AlertTriangle,
  User,
  FileText,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { format, differenceInYears, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import { patientApi } from '@/services/patientApi';
import { PatientDialog } from '@/components/patients/PatientDialog';
import type { PatientListItem, PatientSearchParams } from '@/types/patient';

import { useVirtualizer } from '@tanstack/react-virtual';

export default function PatientList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const parentRef = useRef<HTMLDivElement>(null);
  
  const [patients, setPatients] = useState<PatientListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalPatients, setTotalPatients] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('active');
  const [alertFilter, setAlertFilter] = useState(false);
  const [sortBy, setSortBy] = useState<'name' | 'lastVisit' | 'nextAppointment'>('name');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Dialog state
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  // Load patients
  const loadPatients = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: PatientSearchParams = {
        query: searchQuery || undefined,
        status: statusFilter,
        hasMedicalAlert: alertFilter || undefined,
        sortBy,
        page: currentPage,
        limit: 50, // Increased limit for better scroll experience
      };
      const result = await patientApi.getPatients(params);
      setPatients(result.data);
      setTotalPatients(result.total);
      setTotalPages(result.totalPages);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load patients',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, statusFilter, alertFilter, sortBy, currentPage, toast]);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  const rowVirtualizer = useVirtualizer({
    count: patients.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72,
    overscan: 5,
  });

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setCurrentPage(1);
      loadPatients();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, loadPatients]);

  const handleStatusFilterChange = (value: string) => {
    if (value === 'all' || value === 'active' || value === 'inactive') {
      setStatusFilter(value);
      setCurrentPage(1);
    }
  };

  const handleSortChange = (value: string) => {
    if (value === 'name' || value === 'lastVisit' || value === 'nextAppointment') {
      setSortBy(value);
      setCurrentPage(1);
    }
  };

  const handleViewPatient = (id: string) => {
    navigate(`/patients/${id}`);
  };

  const handlePatientCreated = () => {
    setIsCreateDialogOpen(false);
    loadPatients();
    toast({
      title: 'Patient Created',
      description: 'New patient record has been created',
    });
  };

  const calculateAge = (dob: string) => {
    return differenceInYears(new Date(), parseISO(dob));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Patients</h1>
          <p className="text-muted-foreground">
            {totalPatients} patient{totalPatients !== 1 ? 's' : ''} in directory
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Patient
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, phone, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <div className="flex gap-2">
          <Select value={statusFilter} onValueChange={handleStatusFilterChange}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={sortBy} onValueChange={handleSortChange}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="lastVisit">Last Visit</SelectItem>
              <SelectItem value="nextAppointment">Next Appt</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            variant={alertFilter ? "default" : "outline"}
            size="icon"
            onClick={() => { setAlertFilter(!alertFilter); setCurrentPage(1); }}
            title="Show patients with medical alerts"
          >
            <AlertTriangle className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Patient Table */}
      <div 
        ref={parentRef}
        className="border rounded-lg bg-card overflow-auto max-h-[600px] relative"
      >
        <Table>
          <TableHeader className="sticky top-0 bg-card z-10 shadow-sm">
            <TableRow>
              <TableHead>Patient</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Age</TableHead>
              <TableHead>Last Visit</TableHead>
              <TableHead>Next Appt</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-10 w-48" /></TableCell>
                  <TableCell><Skeleton className="h-10 w-40" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-12" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-16" /></TableCell>
                  <TableCell><Skeleton className="h-8 w-8" /></TableCell>
                </TableRow>
              ))
            ) : patients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center">
                  <div className="flex flex-col items-center justify-center text-muted-foreground">
                    <User className="h-12 w-12 mb-2 opacity-30" />
                    <p>No patients found</p>
                    <p className="text-sm">Try adjusting your search or filters</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const patient = patients[virtualRow.index];
                return (
                  <TableRow 
                    key={patient.id}
                    data-index={virtualRow.index}
                    ref={rowVirtualizer.measureElement}
                    className="cursor-pointer hover:bg-muted/50 absolute top-0 left-0 w-full flex"
                    style={{ transform: `translateY(${virtualRow.start}px)` }}
                    onClick={() => handleViewPatient(patient.id)}
                  >
                    <TableCell className="flex-1">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-sm font-medium text-primary">
                            {patient.firstName[0]}{patient.lastName[0]}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium flex items-center gap-2">
                            {patient.firstName} {patient.lastName}
                            {patient.hasMedicalAlerts && (
                              <AlertTriangle className="h-4 w-4 text-destructive" />
                            )}
                          </div>
                          {patient.hasMedicalAlerts && (
                            <div className="text-xs text-destructive">
                              {patient.medicalAlerts.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="w-[200px]">
                      <div className="text-sm space-y-1">
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Phone className="h-3 w-3" />
                          {patient.phone}
                        </div>
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Mail className="h-3 w-3" />
                          {patient.email}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="w-[80px]">
                      <span className="text-sm">{calculateAge(patient.dateOfBirth)}</span>
                    </TableCell>
                    <TableCell className="w-[120px]">
                      {patient.lastVisit ? (
                        <span className="text-sm">
                          {format(parseISO(patient.lastVisit), 'MMM d, yyyy')}
                        </span>
                      ) : (
                        <span className="text-sm text-muted-foreground">Never</span>
                      )}
                    </TableCell>
                    <TableCell className="w-[120px]">
                      {patient.nextAppointment ? (
                        <div className="flex items-center gap-1 text-sm">
                          <Calendar className="h-3 w-3 text-primary" />
                          {format(parseISO(patient.nextAppointment), 'MMM d')}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="w-[100px]">
                      <Badge variant={patient.status === 'active' ? 'default' : 'secondary'}>
                        {patient.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="w-[50px]">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewPatient(patient.id); }}>
                            <User className="h-4 w-4 mr-2" />
                            View Profile
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); navigate('/schedule'); }}>
                            <Calendar className="h-4 w-4 mr-2" />
                            Schedule Appointment
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); window.location.href = `tel:${patient.phone}`; }}>
                            <Phone className="h-4 w-4 mr-2" />
                            Call Patient
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); window.location.href = `mailto:${patient.email}`; }}>
                            <Mail className="h-4 w-4 mr-2" />
                            Send Email
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <div className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Create Patient Dialog */}
      <PatientDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSave={handlePatientCreated}
      />
    </div>
  );
}
