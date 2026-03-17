// ============================================
// CoreDent PMS - Treatment Plans Page
// Manage treatment plans for patients
// ============================================

import React, { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { Plus, Search, FileText } from 'lucide-react';
import { TreatmentPlanCard } from '@/components/treatment/TreatmentPlanCard';
import { TreatmentPlanDialog } from '@/components/treatment/TreatmentPlanDialog';
import { TreatmentPlanDetails } from '@/components/treatment/TreatmentPlanDetails';
import { treatmentPlanApi } from '@/services/treatmentPlanApi';
import { triggerAutomation } from '@/services/automationApi';
import type { TreatmentPlan, TreatmentStatus, ProcedurePhase } from '@/types/treatmentPlan';

type TabFilter = 'all' | 'active' | 'completed';

export default function TreatmentPlans() {
  const { toast } = useToast();
  
  // State
  const [plans, setPlans] = useState<TreatmentPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<TabFilter>('all');
  
  // Dialog states
  const [isPlanDialogOpen, setIsPlanDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<TreatmentPlan | null>(null);
  const [viewingPlan, setViewingPlan] = useState<TreatmentPlan | null>(null);
  const [deletingPlan, setDeletingPlan] = useState<TreatmentPlan | null>(null);

  // Load plans
  useEffect(() => {
    async function loadPlans() {
      setIsLoading(true);
      try {
        const data = await treatmentPlanApi.getPlans();
        setPlans(data);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to load treatment plans',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    }
    loadPlans();
  }, [toast]);

  // Filter plans
  const filteredPlans = plans.filter(plan => {
    // Search filter
    const matchesSearch = 
      plan.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plan.patientName.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Tab filter
    let matchesTab = true;
    if (activeTab === 'active') {
      matchesTab = ['proposed', 'accepted', 'in_progress'].includes(plan.status);
    } else if (activeTab === 'completed') {
      matchesTab = plan.status === 'completed';
    }
    
    return matchesSearch && matchesTab;
  });

  // Create plan
  const handleCreatePlan = async (data: {
    title: string;
    description?: string;
    patientId: string;
    patientName: string;
    notes?: string;
  }) => {
    try {
      const newPlan = await treatmentPlanApi.createPlan({
        ...data,
        status: 'proposed',
        procedures: [],
        createdBy: 'current-user',
      });
      setPlans(prev => [newPlan, ...prev]);
      toast({
        title: 'Plan created',
        description: `Treatment plan "${data.title}" has been created`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create treatment plan',
        variant: 'destructive',
      });
    }
  };

  // Update plan
  const handleUpdatePlan = async (data: {
    title: string;
    description?: string;
    patientId: string;
    patientName: string;
    notes?: string;
  }) => {
    if (!editingPlan) return;
    
    try {
      const updated = await treatmentPlanApi.updatePlan(editingPlan.id, data);
      setPlans(prev => prev.map(p => p.id === updated.id ? updated : p));
      if (viewingPlan?.id === updated.id) {
        setViewingPlan(updated);
      }
      setEditingPlan(null);
      toast({
        title: 'Plan updated',
        description: 'Treatment plan has been updated',
      });

      // Trigger automation if plan was accepted/approved
      if (updated.status === 'accepted' && editingPlan.status !== 'accepted') {
        const summary = await import('@/types/treatmentPlan').then(m => m.calculatePlanSummary(updated));
        triggerAutomation('treatment_plan_approved', {
          treatmentPlanId: updated.id,
          patientName: updated.patientName,
          totalAmount: summary.totalEstimatedCost,
          procedures: updated.procedures.map(p => p.procedureName),
          clinicName: 'CoreDent Clinic',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update treatment plan',
        variant: 'destructive',
      });
    }
  };

  // Delete plan
  const handleDeletePlan = async () => {
    if (!deletingPlan) return;
    
    try {
      await treatmentPlanApi.deletePlan(deletingPlan.id);
      setPlans(prev => prev.filter(p => p.id !== deletingPlan.id));
      if (viewingPlan?.id === deletingPlan.id) {
        setViewingPlan(null);
      }
      setDeletingPlan(null);
      toast({
        title: 'Plan deleted',
        description: 'Treatment plan has been deleted',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete treatment plan',
        variant: 'destructive',
      });
    }
  };

  // Add procedure to viewing plan
  const handleAddProcedure = async (data: {
    procedureCode: string;
    procedureName: string;
    toothNumber?: number;
    phase: ProcedurePhase;
    estimatedCost: number;
    notes?: string;
  }) => {
    if (!viewingPlan) return;
    
    try {
      const newProcedure = await treatmentPlanApi.addProcedure(viewingPlan.id, {
        ...data,
        status: 'planned',
        dentistId: 'current-user',
        dentistName: 'Dr. Current User',
      });
      
      const updatedPlan = {
        ...viewingPlan,
        procedures: [...viewingPlan.procedures, newProcedure],
      };
      setViewingPlan(updatedPlan);
      setPlans(prev => prev.map(p => p.id === updatedPlan.id ? updatedPlan : p));
      
      toast({
        title: 'Procedure added',
        description: `${data.procedureName} added to treatment plan`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add procedure',
        variant: 'destructive',
      });
    }
  };

  // Complete procedure
  const handleCompleteProcedure = async (procedureId: string) => {
    if (!viewingPlan) return;
    
    try {
      const updatedProcedure = await treatmentPlanApi.completeProcedure(
        viewingPlan.id,
        procedureId
      );
      
      // Refresh the plan to get updated status
      const refreshedPlan = await treatmentPlanApi.getPlan(viewingPlan.id);
      if (refreshedPlan) {
        setViewingPlan(refreshedPlan);
        setPlans(prev => prev.map(p => p.id === refreshedPlan.id ? refreshedPlan : p));
      }
      
      toast({
        title: 'Procedure completed',
        description: 'Procedure has been marked as completed',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to complete procedure',
        variant: 'destructive',
      });
    }
  };

  // Delete procedure
  const handleDeleteProcedure = async (procedureId: string) => {
    if (!viewingPlan) return;
    
    try {
      await treatmentPlanApi.deleteProcedure(viewingPlan.id, procedureId);
      
      const updatedPlan = {
        ...viewingPlan,
        procedures: viewingPlan.procedures.filter(p => p.id !== procedureId),
      };
      setViewingPlan(updatedPlan);
      setPlans(prev => prev.map(p => p.id === updatedPlan.id ? updatedPlan : p));
      
      toast({
        title: 'Procedure removed',
        description: 'Procedure has been removed from the plan',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to remove procedure',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Treatment Plans</h1>
          <p className="text-muted-foreground">
            Create and manage patient treatment plans
          </p>
        </div>
        
        <Button onClick={() => setIsPlanDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Plan
        </Button>
      </div>

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search plans..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabFilter)}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Plans grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-[280px] rounded-xl" />
          ))}
        </div>
      ) : filteredPlans.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 mx-auto text-muted-foreground/50" />
          <h3 className="mt-4 text-lg font-medium">No treatment plans found</h3>
          <p className="text-muted-foreground mt-1">
            {searchQuery
              ? 'Try adjusting your search terms'
              : 'Create a new treatment plan to get started'}
          </p>
          {!searchQuery && (
            <Button className="mt-4" onClick={() => setIsPlanDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Plan
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredPlans.map(plan => (
            <TreatmentPlanCard
              key={plan.id}
              plan={plan}
              onView={setViewingPlan}
              onEdit={setEditingPlan}
              onDelete={setDeletingPlan}
            />
          ))}
        </div>
      )}

      {/* Create/Edit Plan Dialog */}
      <TreatmentPlanDialog
        open={isPlanDialogOpen || !!editingPlan}
        onOpenChange={(open) => {
          if (!open) {
            setIsPlanDialogOpen(false);
            setEditingPlan(null);
          }
        }}
        plan={editingPlan}
        onSubmit={editingPlan ? handleUpdatePlan : handleCreatePlan}
      />

      {/* View Plan Details Sheet */}
      <TreatmentPlanDetails
        open={!!viewingPlan}
        onOpenChange={(open) => !open && setViewingPlan(null)}
        plan={viewingPlan}
        onEdit={() => {
          setEditingPlan(viewingPlan);
        }}
        onAddProcedure={handleAddProcedure}
        onCompleteProcedure={handleCompleteProcedure}
        onDeleteProcedure={handleDeleteProcedure}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deletingPlan} onOpenChange={(open) => !open && setDeletingPlan(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Treatment Plan?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the treatment plan "{deletingPlan?.title}" and all its procedures. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeletePlan}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Plan
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
