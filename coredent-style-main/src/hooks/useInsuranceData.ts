import { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { insuranceApi } from '@/services/insuranceApi';
import type { 
  InsuranceCarrier, 
  InsuranceClaim, 
  InsurancePreAuthorization, 
  InsuranceSummary 
} from '@/types/insurance';

export function useInsuranceData() {
  const [carriers, setCarriers] = useState<InsuranceCarrier[]>([]);
  const [claims, setClaims] = useState<InsuranceClaim[]>([]);
  const [preAuths, setPreAuths] = useState<InsurancePreAuthorization[]>([]);
  const [summary, setSummary] = useState<InsuranceSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [carriersData, claimsData, preAuthsData, summaryData] = await Promise.all([
        insuranceApi.getCarriers(),
        insuranceApi.getClaims(),
        insuranceApi.getPreAuthorizations(),
        insuranceApi.getSummary(),
      ]);
      
      setCarriers(carriersData);
      setClaims(claimsData);
      setPreAuths(preAuthsData);
      setSummary(summaryData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load insurance data',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const refetch = useCallback(async () => {
    await loadData();
  }, [loadData]);

  return {
    carriers,
    claims,
    preAuths,
    summary,
    isLoading,
    refetch,
  };
}