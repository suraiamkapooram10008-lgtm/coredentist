// ============================================
// CoreDent PMS - Treatment Plan Card
// Summary card for a treatment plan
// ============================================

import React from 'react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  MoreVertical, 
  Eye, 
  Edit, 
  Trash2, 
  CheckCircle,
  User,
  Calendar,
  DollarSign
} from 'lucide-react';
import type { TreatmentPlan } from '@/types/treatmentPlan';
import { STATUS_CONFIG, calculatePlanSummary } from '@/types/treatmentPlan';
import { cn } from '@/lib/utils';

interface TreatmentPlanCardProps {
  plan: TreatmentPlan;
  onView: (plan: TreatmentPlan) => void;
  onEdit: (plan: TreatmentPlan) => void;
  onDelete: (plan: TreatmentPlan) => void;
  onComplete?: (plan: TreatmentPlan) => void;
}

export function TreatmentPlanCard({
  plan,
  onView,
  onEdit,
  onDelete,
  onComplete,
}: TreatmentPlanCardProps) {
  const summary = calculatePlanSummary(plan);
  const statusConfig = STATUS_CONFIG[plan.status];
  const progressPercent = summary.totalProcedures > 0
    ? (summary.completedProcedures / summary.totalProcedures) * 100
    : 0;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg truncate">{plan.title}</CardTitle>
            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
              <User className="h-3.5 w-3.5" />
              <span>{plan.patientName}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge className={cn('capitalize', statusConfig.color)}>
              {statusConfig.label}
            </Badge>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onView(plan)}>
                  <Eye className="h-4 w-4 mr-2" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit(plan)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Plan
                </DropdownMenuItem>
                {plan.status === 'in_progress' && onComplete && (
                  <DropdownMenuItem onClick={() => onComplete(plan)}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Mark Complete
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onDelete(plan)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Plan
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {plan.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {plan.description}
          </p>
        )}
        
        {/* Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">
              {summary.completedProcedures} / {summary.totalProcedures} procedures
            </span>
          </div>
          <Progress value={progressPercent} className="h-2" />
        </div>
        
        {/* Cost summary */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Estimated Total
            </p>
            <p className="font-semibold">{formatCurrency(summary.totalEstimatedCost)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Remaining</p>
            <p className="font-semibold text-amber-600">
              {formatCurrency(summary.remainingCost)}
            </p>
          </div>
        </div>
        
        {/* Date */}
        <div className="flex items-center gap-1 text-xs text-muted-foreground pt-2 border-t">
          <Calendar className="h-3 w-3" />
          <span>Created {format(new Date(plan.createdAt), 'MMM d, yyyy')}</span>
          {plan.acceptedAt && (
            <>
              <span>•</span>
              <span>Accepted {format(new Date(plan.acceptedAt), 'MMM d, yyyy')}</span>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
