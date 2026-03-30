// ============================================
// CoreDent PMS - Edit Staff Dialog
// Modal for editing staff member details and role
// ============================================

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Loader2, Shield, AlertTriangle } from 'lucide-react';
import { z } from 'zod';
import { useToast } from '@/hooks/use-toast';
import { rolePermissions } from '@/types/staff';
import type { StaffMember } from '@/types/staff';
import type { UserRole } from '@/types/api';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import { staffApi } from '@/services/staffApi';

const editSchema = z.object({
  firstName: z.string().trim().min(1, 'First name is required').max(50),
  lastName: z.string().trim().min(1, 'Last name is required').max(50),
  role: z.enum(['owner', 'admin', 'dentist', 'front_desk']),
  phone: z.string().optional(),
});

interface EditStaffDialogProps {
  staff: StaffMember | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (staff: StaffMember) => void;
}

export function EditStaffDialog({ staff, open, onOpenChange, onSuccess }: EditStaffDialogProps) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [role, setRole] = useState<UserRole | ''>('');
  const [phone, setPhone] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  // Populate form when staff changes
  useEffect(() => {
    if (staff) {
      setFirstName(staff.firstName);
      setLastName(staff.lastName);
      setRole(staff.role);
      setPhone(staff.phone || '');
    }
  }, [staff]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!staff) return;

    // Validate input
    const result = editSchema.safeParse({ firstName, lastName, role, phone });

    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        const field = issue.path[0] as string;
        fieldErrors[field] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await staffApi.update(staff.id, { firstName, lastName, role, phone });
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to update staff member');
      }

      toast({
        title: 'Staff Updated',
        description: `${firstName} ${lastName}'s information has been updated.`,
      });

      onSuccess?.(response.data);
      onOpenChange(false);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to update staff member. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getInitials = (first: string | undefined, last: string | undefined) => {
    if (!first || !last) return '?';
    return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase();
  };

  const isRoleChange = staff && role !== staff.role;

  if (!staff) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Edit Staff Member
          </DialogTitle>
          <DialogDescription>
            Update staff information and role assignments.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {/* Staff Info Display */}
            <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
              <Avatar className="h-14 w-14">
                <AvatarImage src={staff.avatarUrl} />
                <AvatarFallback className="bg-primary text-primary-foreground text-lg">
                  {getInitials(staff.firstName, staff.lastName)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium">
                  {staff.firstName} {staff.lastName}
                </p>
                <p className="text-sm text-muted-foreground">{staff.email}</p>
                <Badge className={rolePermissions[staff.role].color + ' mt-1'}>
                  Current: {rolePermissions[staff.role].label}
                </Badge>
              </div>
            </div>

            {/* Name Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="editFirstName">First Name</Label>
                <Input
                  id="editFirstName"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className={errors.firstName ? 'border-destructive' : ''}
                  disabled={isSubmitting}
                />
                {errors.firstName && (
                  <p className="text-sm text-destructive">{errors.firstName}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="editLastName">Last Name</Label>
                <Input
                  id="editLastName"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className={errors.lastName ? 'border-destructive' : ''}
                  disabled={isSubmitting}
                />
                {errors.lastName && (
                  <p className="text-sm text-destructive">{errors.lastName}</p>
                )}
              </div>
            </div>

            {/* Phone Field */}
            <div className="space-y-2">
              <Label htmlFor="editPhone">Phone Number</Label>
              <Input
                id="editPhone"
                type="tel"
                placeholder="(555) 123-4567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            {/* Role Selection */}
            <div className="space-y-2">
              <Label htmlFor="editRole">Role</Label>
              <Select
                value={role}
                onValueChange={(value: UserRole) => setRole(value)}
                disabled={isSubmitting}
              >
                <SelectTrigger className={errors.role ? 'border-destructive' : ''}>
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(rolePermissions).map(([key, info]) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-2">
                        <span>{info.label}</span>
                        <span className="text-xs text-muted-foreground">
                          - {info.description.slice(0, 30)}...
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.role && (
                <p className="text-sm text-destructive">{errors.role}</p>
              )}
            </div>

            {/* Role Change Warning */}
            {isRoleChange && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Role Change</AlertTitle>
                <AlertDescription>
                  Changing the role will immediately update this user's permissions.
                  They will gain or lose access to features based on the new role.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting} className="gap-2">
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
