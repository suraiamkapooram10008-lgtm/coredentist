// ============================================
// CoreDent PMS - Staff Settings Tab
// Embedded staff management with confirmations
// ============================================

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Search,
  UserPlus,
  MoreHorizontal,
  Mail,
  Shield,
  UserX,
  UserCheck,
  Clock,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { rolePermissions } from '@/types/staff';
import type { StaffMember, StaffInvitation } from '@/types/staff';
import { InviteStaffDialog } from '@/components/admin/InviteStaffDialog';
import { EditStaffDialog } from '@/components/admin/EditStaffDialog';
import { ConfirmationDialog } from '@/components/settings/ConfirmationDialog';
import { formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { staffApi } from '@/services/staffApi';

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
};

export function StaffSettingsTab() {
  const { toast } = useToast();
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [invitations, setInvitations] = useState<StaffInvitation[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState<StaffMember | null>(null);
  
  // Confirmation dialogs
  const [deactivateConfirm, setDeactivateConfirm] = useState<StaffMember | null>(null);
  const [cancelInviteConfirm, setCancelInviteConfirm] = useState<StaffInvitation | null>(null);

  useEffect(() => {
    let isActive = true;
    const loadStaff = async () => {
      try {
        const [staffResponse, invitationsResponse] = await Promise.all([
          staffApi.list(),
          staffApi.listInvitations(),
        ]);
        if (!isActive) return;
        if (staffResponse.success && staffResponse.data) {
          setStaff(staffResponse.data.data);
        } else {
          setStaff([]);
          toast({
            title: 'Error',
            description: staffResponse.error?.message || 'Failed to load staff',
            variant: 'destructive',
          });
        }
        if (invitationsResponse.success && invitationsResponse.data) {
          setInvitations(invitationsResponse.data);
        } else {
          setInvitations([]);
          toast({
            title: 'Error',
            description: invitationsResponse.error?.message || 'Failed to load invitations',
            variant: 'destructive',
          });
        }
      } catch (error) {
        if (!isActive) return;
        setStaff([]);
        setInvitations([]);
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to load staff data',
          variant: 'destructive',
        });
      }
    };
    loadStaff();
    return () => {
      isActive = false;
    };
  }, [toast]);

  // Filter staff based on search and filters
  const filteredStaff = staff.filter((member) => {
    const matchesSearch =
      searchQuery === '' ||
      `${member.firstName} ${member.lastName}`.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = roleFilter === 'all' || member.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || member.status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const handleDeactivate = async () => {
    if (!deactivateConfirm) return;
    
    try {
      const response = await staffApi.deactivate(deactivateConfirm.id);
      if (response.success && response.data) {
        setStaff(prev => prev.map(s => s.id === deactivateConfirm.id ? response.data! : s));
      } else {
        throw new Error(response.error?.message || 'Failed to deactivate staff');
      }
      toast({
        title: 'Staff deactivated',
        description: `${deactivateConfirm.firstName} ${deactivateConfirm.lastName} has been deactivated`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to deactivate staff',
        variant: 'destructive',
      });
    }
  };

  const handleReactivate = async (member: StaffMember) => {
    try {
      const response = await staffApi.reactivate(member.id);
      if (response.success && response.data) {
        setStaff(prev => prev.map(s => s.id === member.id ? response.data! : s));
      } else {
        throw new Error(response.error?.message || 'Failed to reactivate staff');
      }
      toast({
        title: 'Staff reactivated',
        description: `${member.firstName} ${member.lastName} has been reactivated`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to reactivate staff',
        variant: 'destructive',
      });
    }
  };

  const handleCancelInvitation = async () => {
    if (!cancelInviteConfirm) return;
    
    try {
      await staffApi.cancelInvitation(cancelInviteConfirm.id);
      setInvitations(prev => prev.filter(i => i.id !== cancelInviteConfirm.id));
      toast({
        title: 'Invitation cancelled',
        description: `Invitation to ${cancelInviteConfirm.email} has been cancelled`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to cancel invitation',
        variant: 'destructive',
      });
    }
  };

  const handleResendInvitation = async (invitation: StaffInvitation) => {
    try {
      const response = await staffApi.resendInvitation(invitation.id);
      if (response.success && response.data) {
        setInvitations(prev => prev.map(i => i.id === invitation.id ? response.data! : i));
      } else {
        throw new Error(response.error?.message || 'Failed to resend invitation');
      }
      toast({
        title: 'Invitation resent',
        description: `A new invitation has been sent to ${invitation.email}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to resend invitation',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Invite Button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Staff Management</h2>
          <p className="text-sm text-muted-foreground">
            Manage team members, roles, and invitations
          </p>
        </div>
        <Button onClick={() => setIsInviteOpen(true)} className="gap-2">
          <UserPlus className="h-4 w-4" />
          Invite Staff
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Staff</p>
                <p className="text-2xl font-bold">{staff.length}</p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <Shield className="h-5 w-5 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active</p>
                <p className="text-2xl font-bold">
                  {staff.filter((s) => s.status === 'active').length}
                </p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                <UserCheck className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending Invites</p>
                <p className="text-2xl font-bold">{invitations.length}</p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900">
                <Clock className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Dentists</p>
                <p className="text-2xl font-bold">
                  {staff.filter((s) => s.role === 'dentist').length}
                </p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Staff and Invitations */}
      <Tabs defaultValue="staff" className="space-y-4">
        <TabsList>
          <TabsTrigger value="staff">Staff Members</TabsTrigger>
          <TabsTrigger value="invitations">
            Pending Invitations
            {invitations.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {invitations.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Staff Members Tab */}
        <TabsContent value="staff">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row gap-4">
                {/* Search */}
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search by name or email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                {/* Filters */}
                <div className="flex gap-2">
                  <Select value={roleFilter} onValueChange={setRoleFilter}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Roles</SelectItem>
                      <SelectItem value="owner">Owner</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="dentist">Dentist</SelectItem>
                      <SelectItem value="front_desk">Front Desk</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Active</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStaff.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        No staff members found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredStaff.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar>
                              <AvatarImage src={member.avatarUrl} />
                              <AvatarFallback className="bg-primary text-primary-foreground">
                                {getInitials(member.firstName, member.lastName)}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <div className="font-medium">
                                {member.firstName} {member.lastName}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {member.email}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={rolePermissions[member.role].color}>
                            {rolePermissions[member.role].label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[member.status]}>
                            {member.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {member.lastLoginAt
                            ? formatDistanceToNow(new Date(member.lastLoginAt), {
                                addSuffix: true,
                              })
                            : 'Never'}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => setEditingStaff(member)}>
                                <Shield className="mr-2 h-4 w-4" />
                                Edit Role
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Mail className="mr-2 h-4 w-4" />
                                Send Message
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              {member.status === 'active' ? (
                                <DropdownMenuItem 
                                  className="text-destructive"
                                  onClick={() => setDeactivateConfirm(member)}
                                >
                                  <UserX className="mr-2 h-4 w-4" />
                                  Deactivate
                                </DropdownMenuItem>
                              ) : (
                                <DropdownMenuItem onClick={() => handleReactivate(member)}>
                                  <UserCheck className="mr-2 h-4 w-4" />
                                  Reactivate
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pending Invitations Tab */}
        <TabsContent value="invitations">
          <Card>
            <CardHeader>
              <CardTitle>Pending Invitations</CardTitle>
              <CardDescription>
                Staff members who haven't accepted their invitation yet
              </CardDescription>
            </CardHeader>
            <CardContent>
              {invitations.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Mail className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium">No pending invitations</h3>
                  <p className="text-muted-foreground">
                    All invited staff have accepted their invitations
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Invited By</TableHead>
                      <TableHead>Expires</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invitations.map((invitation) => (
                      <TableRow key={invitation.id}>
                        <TableCell className="font-medium">
                          {invitation.email}
                        </TableCell>
                        <TableCell>
                          <Badge className={rolePermissions[invitation.role].color}>
                            {rolePermissions[invitation.role].label}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {invitation.invitedByName}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDistanceToNow(new Date(invitation.expiresAt), {
                            addSuffix: true,
                          })}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              title="Resend"
                              onClick={() => handleResendInvitation(invitation)}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-destructive"
                              title="Cancel"
                              onClick={() => setCancelInviteConfirm(invitation)}
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <InviteStaffDialog
        open={isInviteOpen}
        onOpenChange={setIsInviteOpen}
        onSuccess={(invitation) => setInvitations((prev) => [invitation, ...prev])}
      />
      
      {editingStaff && (
        <EditStaffDialog
          staff={editingStaff}
          open={!!editingStaff}
          onOpenChange={(open) => !open && setEditingStaff(null)}
          onSuccess={(updated) =>
            setStaff((prev) => prev.map((member) => (member.id === updated.id ? updated : member)))
          }
        />
      )}

      {/* Deactivate Confirmation */}
      <ConfirmationDialog
        open={!!deactivateConfirm}
        onOpenChange={(open) => !open && setDeactivateConfirm(null)}
        title="Deactivate Staff Member"
        description={`Are you sure you want to deactivate ${deactivateConfirm?.firstName} ${deactivateConfirm?.lastName}? They will no longer be able to access the system until reactivated.`}
        type="deactivate"
        confirmText="Deactivate"
        onConfirm={handleDeactivate}
      />

      {/* Cancel Invitation Confirmation */}
      <ConfirmationDialog
        open={!!cancelInviteConfirm}
        onOpenChange={(open) => !open && setCancelInviteConfirm(null)}
        title="Cancel Invitation"
        description={`Are you sure you want to cancel the invitation to ${cancelInviteConfirm?.email}? They will need a new invitation to join the practice.`}
        type="warning"
        confirmText="Cancel Invitation"
        onConfirm={handleCancelInvitation}
      />
    </div>
  );
}
