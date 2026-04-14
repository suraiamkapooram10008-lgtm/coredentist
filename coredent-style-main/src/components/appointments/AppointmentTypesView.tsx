/**
 * AppointmentTypesView Component
 * Displays appointment types configuration
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

interface AppointmentType {
  id: string;
  name: string;
  duration: number;
}

interface AppointmentTypesViewProps {
  types: AppointmentType[];
  onAddType?: () => void;
}

/**
 * View for managing appointment types
 */
export const AppointmentTypesView = React.memo(function AppointmentTypesView({
  types,
  onAddType,
}: AppointmentTypesViewProps) {
  if (types.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Appointment Types</CardTitle>
            <Button variant="outline" onClick={onAddType}>
              <Plus className="mr-2 h-4 w-4" />
              Add Type
            </Button>
          </div>
        </CardHeader>
        <CardContent className="text-center py-8 text-muted-foreground">
          No appointment types configured
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Appointment Types</CardTitle>
          <Button variant="outline" onClick={onAddType}>
            <Plus className="mr-2 h-4 w-4" />
            Add Type
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {types.map((type) => (
            <div
              key={type.id}
              className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
            >
              <h4 className="font-medium">{type.name}</h4>
              <p className="text-sm text-muted-foreground">{type.duration} minutes</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
});
