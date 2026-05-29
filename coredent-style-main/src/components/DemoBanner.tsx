import { Construction } from 'lucide-react';

export function DemoBanner() {
  return (
    <div className="flex items-center gap-3 p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg mb-6">
      <Construction className="h-5 w-5 text-amber-600 flex-shrink-0" />
      <p className="text-sm text-amber-800 dark:text-amber-200">
        <strong>Demo Mode:</strong> This page uses simulated data. Full API integration is coming soon.
      </p>
    </div>
  );
}