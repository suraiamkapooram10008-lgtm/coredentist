import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, subDays } from 'date-fns';
import {
  Activity,
  Building2,
  CalendarRange,
  CircleDollarSign,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Users,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ApiResponse } from '@/types/api';
import {
  enterpriseApi,
  type EnterpriseGroupAnalytics,
  type EnterprisePractice,
} from '@/services/enterpriseApi';

interface DateRange {
  start: string;
  end: string;
}

function unwrapResponse<T>(response: ApiResponse<T>): T {
  if (!response.success || response.data === undefined) {
    throw new Error(response.error?.message || 'The enterprise service is unavailable.');
  }
  return response.data;
}

function formatMetric(value: number): string {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}

function formatPeriod(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : format(date, 'MMM d, yyyy');
}

function MetricCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof CircleDollarSign;
}) {
  return (
    <Card className="rounded-2xl border-slate-200 shadow-sm">
      <CardContent className="flex items-center gap-4 p-6">
        <div className="rounded-xl bg-slate-100 p-3 text-slate-700">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-black text-slate-900">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function EnterpriseHQ() {
  const dateRange = useMemo<DateRange>(() => {
    const end = new Date();
    return {
      start: format(subDays(end, 29), 'yyyy-MM-dd'),
      end: format(end, 'yyyy-MM-dd'),
    };
  }, []);

  const analyticsQuery = useQuery<EnterpriseGroupAnalytics>({
    queryKey: ['enterprise', 'group-analytics', dateRange.start, dateRange.end],
    queryFn: async () =>
      unwrapResponse(
        await enterpriseApi.getGroupAnalytics({
          start_date: dateRange.start,
          end_date: dateRange.end,
        }),
      ),
    staleTime: 60_000,
  });

  const practicesQuery = useQuery<EnterprisePractice[]>({
    queryKey: ['enterprise', 'group-practices'],
    queryFn: async () => unwrapResponse(await enterpriseApi.listGroupPractices({ page: 1, limit: 100 })),
    staleTime: 5 * 60_000,
  });

  const analytics = analyticsQuery.data;
  const practicesById = new Map(
    (practicesQuery.data ?? []).map((practice) => [practice.id, practice]),
  );
  const locations = analytics?.by_location ?? [];
  const periodLabel = analytics
    ? `${formatPeriod(analytics.period.start)} – ${formatPeriod(analytics.period.end)}`
    : `${dateRange.start} – ${dateRange.end}`;

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6 md:p-10">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3">
            <Building2 className="h-8 w-8 text-indigo-600" aria-hidden="true" />
            <h1 className="text-3xl font-black text-slate-900">Enterprise HQ</h1>
            <Badge variant="secondary">Group scope</Badge>
          </div>
          <p className="mt-2 flex items-center gap-2 text-sm text-slate-500">
            <CalendarRange className="h-4 w-4" aria-hidden="true" />
            Authorized group analytics for {periodLabel}.
          </p>
        </div>
        <Button
          variant="outline"
          className="rounded-xl"
          onClick={() => {
            void analyticsQuery.refetch();
            void practicesQuery.refetch();
          }}
          disabled={analyticsQuery.isFetching || practicesQuery.isFetching}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${analyticsQuery.isFetching || practicesQuery.isFetching ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          Refresh data
        </Button>
      </div>

      {analyticsQuery.isLoading && (
        <Card>
          <CardContent className="p-8 text-center text-slate-500">Loading live group analytics…</CardContent>
        </Card>
      )}

      {analyticsQuery.isError && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-start gap-3 p-6 text-amber-950">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-bold">Group analytics unavailable</p>
              <p className="mt-1 text-sm">
                The server did not authorize or return enterprise data. No practice-level or sample numbers are shown.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {analytics && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Group production" value={formatMetric(analytics.consolidated.production)} icon={CircleDollarSign} />
            <MetricCard label="Group collections" value={formatMetric(analytics.consolidated.collections)} icon={CircleDollarSign} />
            <MetricCard label="New patients" value={formatMetric(analytics.consolidated.new_patients)} icon={Users} />
            <MetricCard label="Average utilization" value={`${formatMetric(analytics.consolidated.avg_utilization)}%`} icon={Activity} />
          </div>

          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                Location performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {locations.length === 0 ? (
                <p className="text-sm text-slate-500">No location data is available for this period.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[680px] text-left text-sm">
                    <thead className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                      <tr>
                        <th className="px-3 py-3 font-bold">Location</th>
                        <th className="px-3 py-3 text-right font-bold">Production</th>
                        <th className="px-3 py-3 text-right font-bold">Collections</th>
                        <th className="px-3 py-3 text-right font-bold">New patients</th>
                        <th className="px-3 py-3 text-right font-bold">Utilization</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {locations.map((location) => {
                        const practice = practicesById.get(location.practice_id);
                        return (
                          <tr key={location.practice_id} className="text-slate-700">
                            <td className="px-3 py-4">
                              <p className="font-semibold text-slate-900">{location.practice_name}</p>
                              {practice?.address_city || practice?.address_state ? (
                                <p className="mt-1 text-xs text-slate-500">
                                  {[practice.address_city, practice.address_state].filter(Boolean).join(', ')}
                                </p>
                              ) : null}
                            </td>
                            <td className="px-3 py-4 text-right font-medium">{formatMetric(location.production)}</td>
                            <td className="px-3 py-4 text-right font-medium">{formatMetric(location.collections)}</td>
                            <td className="px-3 py-4 text-right font-medium">{formatMetric(location.new_patients)}</td>
                            <td className="px-3 py-4 text-right font-medium">{formatMetric(location.utilization)}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {practicesQuery.isError && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-start gap-3 p-6 text-amber-950">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-bold">Location directory unavailable</p>
              <p className="mt-1 text-sm">Analytics remain visible, but location address details could not be loaded.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {!analyticsQuery.isLoading && !analyticsQuery.isError && !analytics && (
        <Card>
          <CardContent className="p-8 text-center text-slate-500">No group analytics were returned.</CardContent>
        </Card>
      )}
    </div>
  );
}
