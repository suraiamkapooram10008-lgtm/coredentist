// ============================================
// CoreDent PMS - Insurance Page
// Insurance management and claims tracking
// ============================================

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Plus,
  Search,
  Shield,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
} from 'lucide-react';
import { insuranceApi } from '@/services/insuranceApi';
import type { InsuranceCarrier, InsuranceClaim, InsurancePreAuthorization, InsuranceSummary } from '@/types/insurance';

export default function Insurance() {
  const { toast } = useToast();

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('claims');

  // Load data with React Query
  const { 
    data: carriers = [], 
    isLoading: isLoadingCarriers 
  } = useQuery({
    queryKey: ['insurance', 'carriers'],
    queryFn: () => insuranceApi.getCarriers(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { 
    data: claims = [], 
    isLoading: isLoadingClaims 
  } = useQuery({
    queryKey: ['insurance', 'claims'],
    queryFn: () => insuranceApi.getClaims(),
    staleTime: 5 * 60 * 1000,
  });

  const { 
    data: preAuths = [], 
    isLoading: isLoadingPreAuths 
  } = useQuery({
    queryKey: ['insurance', 'preAuths'],
    queryFn: () => insuranceApi.getPreAuthorizations(),
    staleTime: 5 * 60 * 1000,
  });

  const { 
    data: summary, 
    isLoading: isLoadingSummary 
  } = useQuery({
    queryKey: ['insurance', 'summary'],
    queryFn: () => insuranceApi.getSummary(),
    staleTime: 5 * 60 * 1000,
  });

  const isLoading = isLoadingCarriers || isLoadingClaims || isLoadingPreAuths || isLoadingSummary;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Title */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Insurance Management</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Claim
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Claims</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{summary?.totalClaims || 0}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{summary?.pendingClaims || 0}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">{summary?.approvedClaims || 0}</div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Paid</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <div className="text-2xl font-bold">${summary?.totalPaid?.toLocaleString() || 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="claims">Claims</TabsTrigger>
          <TabsTrigger value="eligibility">Eligibility</TabsTrigger>
          <TabsTrigger value="eobs">EOBs</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="claims">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                <Input
                  placeholder="Search claims..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="max-w-sm"
                />
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : (
                <div className="space-y-2">
                  {claims.length === 0 ? (
                    <p className="text-muted-foreground">No claims found</p>
                  ) : (
                    claims.map((claim) => (
                      <div key={claim.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <Shield className="h-5 w-5" />
                          <div>
                            <p className="font-medium">{claim.patientName}</p>
                            <p className="text-sm text-muted-foreground">{claim.claimNumber}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            claim.status === 'accepted' || claim.status === 'paid' ? 'bg-green-100 text-green-800' :
                            claim.status === 'submitted' || claim.status === 'draft' || claim.status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {claim.status}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            ${claim.totalAmount?.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="eligibility">
          <Card>
            <CardHeader>
              <CardTitle>Insurance Eligibility</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-32 w-full" />
              ) : (
                <div className="space-y-2">
                  {carriers.length === 0 ? (
                    <p className="text-muted-foreground">No insurance carriers found</p>
                  ) : (
                    carriers.map((carrier) => (
                      <div key={carrier.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <Shield className="h-5 w-5" />
                          <div>
                            <p className="font-medium">{carrier.name}</p>
                            <p className="text-sm text-muted-foreground">{carrier.payerId || 'No Payer ID'}</p>
                          </div>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {carrier.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="eobs">
          <Card>
            <CardHeader>
              <CardTitle>Explanation of Benefits</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">EOB documents will appear here</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>Insurance Reports</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Reports will appear here</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
