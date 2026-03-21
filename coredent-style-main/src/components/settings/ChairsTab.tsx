// ============================================
// CoreDent PMS - Chairs/Operatories Tab
// Configure dental chairs and treatment rooms
// ============================================

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Armchair, Plus, Pencil, Trash2, Loader2, Save } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { z } from 'zod';
import type { Chair } from '@/types/clinic';
import { clinicApi } from '@/services/clinicApi';

const chairSchema = z.object({
  name: z.string().trim().min(1, 'Chair name is required').max(50),
  description: z.string().max(200).optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Please select a valid color'),
});

interface ChairsTabProps {
  chairs: Chair[];
  onUpdate: (chairs: Chair[]) => void;
}

const PRESET_COLORS = [
  '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444',
  '#EC4899', '#6366F1', '#14B8A6', '#F97316', '#84CC16',
];

export function ChairsTab({ chairs, onUpdate }: ChairsTabProps) {
  const [chairList, setChairList] = useState<Chair[]>([...chairs]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingChair, setEditingChair] = useState<Chair | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', color: '#3B82F6' });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const openAddDialog = () => {
    setEditingChair(null);
    setFormData({ name: '', description: '', color: '#3B82F6' });
    setErrors({});
    setIsDialogOpen(true);
  };

  const openEditDialog = (chair: Chair) => {
    setEditingChair(chair);
    setFormData({
      name: chair.name,
      description: chair.description || '',
      color: chair.color,
    });
    setErrors({});
    setIsDialogOpen(true);
  };

  const handleSubmit = () => {
    setErrors({});

    const result = chairSchema.safeParse(formData);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        fieldErrors[issue.path[0] as string] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    if (editingChair) {
      // Update existing chair
      setChairList(prev =>
        prev.map(c =>
          c.id === editingChair.id
            ? { ...c, name: formData.name, description: formData.description, color: formData.color }
            : c
        )
      );
      toast({ title: 'Chair Updated', description: `${formData.name} has been updated.` });
    } else {
      // Add new chair
      const newChair: Chair = {
        id: Date.now().toString(),
        name: formData.name,
        description: formData.description,
        color: formData.color,
        isActive: true,
      };
      setChairList(prev => [...prev, newChair]);
      toast({ title: 'Chair Added', description: `${formData.name} has been added.` });
    }

    setIsDialogOpen(false);
  };

  const toggleChairStatus = (id: string) => {
    setChairList(prev =>
      prev.map(c => (c.id === id ? { ...c, isActive: !c.isActive } : c))
    );
  };

  const deleteChair = (id: string) => {
    const chair = chairList.find(c => c.id === id);
    setChairList(prev => prev.filter(c => c.id !== id));
    toast({
      title: 'Chair Deleted',
      description: `${chair?.name} has been removed.`,
    });
  };

  const handleSaveAll = async () => {
    setIsSaving(true);

    try {
      const response = await clinicApi.updateSettings({ chairs: chairList });
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to save chairs');
      }
      setChairList(response.data.chairs);
      onUpdate(response.data.chairs);
      toast({ title: 'Saved', description: 'Chair configuration has been saved.' });
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Armchair className="h-5 w-5" />
              Chairs & Operatories
            </CardTitle>
            <CardDescription>
              Manage your dental chairs and treatment rooms
            </CardDescription>
          </div>
          <Button onClick={openAddDialog} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Chair
          </Button>
        </CardHeader>
        <CardContent>
          {chairList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Armchair className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No chairs configured</h3>
              <p className="text-muted-foreground">Add your first operatory to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chair</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {chairList.map((chair) => (
                  <TableRow key={chair.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div
                          className="h-4 w-4 rounded-full"
                          style={{ backgroundColor: chair.color }}
                        />
                        <span className="font-medium">{chair.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {chair.description || '—'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={chair.isActive}
                          onCheckedChange={() => toggleChairStatus(chair.id)}
                        />
                        <Badge variant={chair.isActive ? 'default' : 'secondary'}>
                          {chair.isActive ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEditDialog(chair)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive"
                          onClick={() => deleteChair(chair.id)}
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
              Save Chairs
            </>
          )}
        </Button>
      </div>

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingChair ? 'Edit Chair' : 'Add New Chair'}
            </DialogTitle>
            <DialogDescription>
              Configure the operatory details
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="chairName">Name *</Label>
              <Input
                id="chairName"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className={errors.name ? 'border-destructive' : ''}
                placeholder="Operatory 1"
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="chairDescription">Description</Label>
              <Input
                id="chairDescription"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Main treatment room"
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
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {editingChair ? 'Update' : 'Add'} Chair
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
