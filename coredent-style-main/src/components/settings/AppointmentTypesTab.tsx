// ============================================
// CoreDent PMS - Appointment Types Tab
// Configure appointment types and durations
// ============================================

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import { Calendar, Plus, Pencil, Trash2, Loader2, Save, Clock, Globe } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { z } from 'zod';
import type { AppointmentTypeConfig } from '@/types/clinic';
import { clinicApi } from '@/services/clinicApi';

const appointmentTypeSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(50),
  code: z.string().trim().min(1, 'Code is required').max(10),
  duration: z.number().min(5, 'Minimum 5 minutes').max(480, 'Maximum 8 hours'),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Please select a valid color'),
  description: z.string().max(200).optional(),
  allowOnlineBooking: z.boolean(),
});

interface AppointmentTypesTabProps {
  appointmentTypes: AppointmentTypeConfig[];
  onUpdate: (types: AppointmentTypeConfig[]) => void;
}

const PRESET_COLORS = [
  '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444',
  '#EC4899', '#6366F1', '#14B8A6', '#F97316', '#84CC16',
];

const DURATION_OPTIONS = [
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 45, label: '45 min' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
  { value: 180, label: '3 hours' },
];

export function AppointmentTypesTab({ appointmentTypes, onUpdate }: AppointmentTypesTabProps) {
  const [types, setTypes] = useState<AppointmentTypeConfig[]>([...appointmentTypes]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingType, setEditingType] = useState<AppointmentTypeConfig | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    duration: 30,
    color: '#3B82F6',
    description: '',
    allowOnlineBooking: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    setTypes([...appointmentTypes]);
  }, [appointmentTypes]);

  const openAddDialog = () => {
    setEditingType(null);
    setFormData({
      name: '',
      code: '',
      duration: 30,
      color: '#3B82F6',
      description: '',
      allowOnlineBooking: false,
    });
    setErrors({});
    setIsDialogOpen(true);
  };

  const openEditDialog = (type: AppointmentTypeConfig) => {
    setEditingType(type);
    setFormData({
      name: type.name,
      code: type.code,
      duration: type.duration,
      color: type.color,
      description: type.description || '',
      allowOnlineBooking: type.allowOnlineBooking,
    });
    setErrors({});
    setIsDialogOpen(true);
  };

  const handleSubmit = () => {
    setErrors({});

    const result = appointmentTypeSchema.safeParse(formData);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        fieldErrors[issue.path[0] as string] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    if (editingType) {
      // Update existing type
      setTypes(prev =>
        prev.map(t =>
          t.id === editingType.id
            ? { ...t, ...formData }
            : t
        )
      );
      toast({ title: 'Updated', description: `${formData.name} has been updated.` });
    } else {
      // Add new type
      const newType: AppointmentTypeConfig = {
        id: Date.now().toString(),
        ...formData,
        isActive: true,
      };
      setTypes(prev => [...prev, newType]);
      toast({ title: 'Added', description: `${formData.name} has been added.` });
    }

    setIsDialogOpen(false);
  };

  const toggleTypeStatus = (id: string) => {
    setTypes(prev =>
      prev.map(t => (t.id === id ? { ...t, isActive: !t.isActive } : t))
    );
  };

  const deleteType = (id: string) => {
    const type = types.find(t => t.id === id);
    setTypes(prev => prev.filter(t => t.id !== id));
    toast({
      title: 'Deleted',
      description: `${type?.name} has been removed.`,
    });
  };

  const handleSaveAll = async () => {
    setIsSaving(true);

    try {
      const response = await clinicApi.updateSettings({ appointmentTypes: types });
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to save appointment types');
      }
      setTypes(response.data.appointmentTypes);
      onUpdate(response.data.appointmentTypes);
      toast({ title: 'Saved', description: 'Appointment types have been saved.' });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to save. Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours} hour${hours > 1 ? 's' : ''}`;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Appointment Types
            </CardTitle>
            <CardDescription>
              Configure the types of appointments your practice offers
            </CardDescription>
          </div>
          <Button onClick={openAddDialog} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Type
          </Button>
        </CardHeader>
        <CardContent>
          {types.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No appointment types</h3>
              <p className="text-muted-foreground">Add your first appointment type</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Online Booking</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {types.map((type) => (
                  <TableRow key={type.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div
                          className="h-4 w-4 rounded-full"
                          style={{ backgroundColor: type.color }}
                        />
                        <span className="font-medium">{type.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-sm bg-muted px-1.5 py-0.5 rounded">
                        {type.code}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatDuration(type.duration)}
                      </div>
                    </TableCell>
                    <TableCell>
                      {type.allowOnlineBooking ? (
                        <Badge variant="secondary" className="gap-1">
                          <Globe className="h-3 w-3" />
                          Enabled
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={type.isActive}
                          onCheckedChange={() => toggleTypeStatus(type.id)}
                        />
                        <Badge variant={type.isActive ? 'default' : 'secondary'}>
                          {type.isActive ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(type)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive"
                          onClick={() => deleteType(type.id)}
                        >
                          <Trash2 className="h-4 w-4" />
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

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSaveAll} disabled={isSaving} size="lg" className="gap-2">
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Types
            </>
          )}
        </Button>
      </div>

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingType ? 'Edit Appointment Type' : 'Add Appointment Type'}
            </DialogTitle>
            <DialogDescription>
              Configure the appointment type details
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="typeName">Name *</Label>
                <Input
                  id="typeName"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={errors.name ? 'border-destructive' : ''}
                  placeholder="Cleaning"
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="typeCode">Code *</Label>
                <Input
                  id="typeCode"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  className={errors.code ? 'border-destructive' : ''}
                  placeholder="D1110"
                />
                {errors.code && (
                  <p className="text-sm text-destructive">{errors.code}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="typeDuration">Duration *</Label>
              <Select
                value={formData.duration.toString()}
                onValueChange={(value) => setFormData({ ...formData, duration: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DURATION_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value.toString()}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="typeDescription">Description</Label>
              <Input
                id="typeDescription"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Routine dental cleaning and checkup"
              />
            </div>

            <div className="space-y-2">
              <Label>Color</Label>
              <div className="flex flex-wrap gap-2">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    className={`h-8 w-8 rounded-full border-2 transition-all ${
                      formData.color === color
                        ? 'border-foreground scale-110'
                        : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                    onClick={() => setFormData({ ...formData, color })}
                  />
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="allowOnlineBooking"
                checked={formData.allowOnlineBooking}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, allowOnlineBooking: checked === true })
                }
              />
              <Label htmlFor="allowOnlineBooking" className="text-sm font-normal">
                Allow patients to book this appointment type online
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {editingType ? 'Update' : 'Add'} Type
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
