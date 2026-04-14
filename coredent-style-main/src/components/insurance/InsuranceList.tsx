import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Search, Plus, Edit, Trash2, FileText } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { insuranceApi } from '@/services/insuranceApi';
import type { InsuranceCarrier } from '@/types/insurance';

interface InsuranceListProps {
  onEdit?: (carrier: InsuranceCarrier) => void;
  onDelete?: (id: string) => void;
  onCreate?: () => void;
}

export function InsuranceList({ onEdit, onDelete, onCreate }: InsuranceListProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');

  const { data: carriers, isLoading, error } = useQuery({
    queryKey: ['insurance-carriers'],
    queryFn: () => insuranceApi.getCarriers(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => insuranceApi.deleteCarrier(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insurance-carriers'] });
      toast({
        title: 'Success',
        description: 'Insurance carrier deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete insurance carrier',
        variant: 'destructive',
      });
    },
  });

  const handleDelete = (id: string) => {
    if (!window.confirm('Are you sure you want to delete this insurance carrier?')) {
      return;
    }
    deleteMutation.mutate(id);
    if (onDelete) onDelete(id);
  };

  const filteredCarriers = carriers?.filter(carrier =>
    carrier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    carrier.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    carrier.phone?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    carrier.payerId?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        Failed to load insurance carriers
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <CardTitle>Insurance Carriers</CardTitle>
          <p className="text-sm text-muted-foreground">
            Manage insurance carriers and their details
          </p>
        </div>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search carriers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button onClick={() => onCreate?.()}>
            <Plus className="mr-2 h-4 w-4" />
            Add Carrier
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {filteredCarriers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            {searchTerm ? 'No carriers found matching your search' : 'No insurance carriers yet'}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredCarriers.map((carrier) => (
              <div
                key={carrier.id}
                className="flex flex-col sm:flex-row gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">{carrier.name}</h3>
                    {carrier.isActive && <Badge className="bg-green-500">Active</Badge>}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                    <div>
                      <span className="font-medium">Phone:</span>
                      <span className="ml-2">{carrier.phone || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="font-medium">Email:</span>
                      <span className="ml-2">{carrier.email || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="font-medium">Payer ID:</span>
                      <span className="ml-2">{carrier.payerId || 'N/A'}</span>
                    </div>
                  </div>
                  {carrier.address && (
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium">Address:</span> {carrier.address}
                      {carrier.city && `, ${carrier.city}`}
                      {carrier.state && `, ${carrier.state}`}
                      {carrier.zipCode && ` ${carrier.zipCode}`}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onEdit?.(carrier)}
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => { /* View claims logic */ }}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Claims
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(carrier.id)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
