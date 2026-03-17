// ============================================
// CoreDent PMS - Insurance Page
// Insurance management and claims tracking
// ============================================

import React, { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
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
  const [carriers, setCarriers] = useState<InsuranceCarrier[]>([]);
  const [claims, setClaims] = useState<InsuranceClaim[]>([]);
  const [preAuths, setPreAuths] = useState<InsurancePreAuthorization[]>([]);
  const [summary, setSummary] = useState<InsuranceSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('carriers');

  // Load data
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [carriersData, claimsData, preAuthsData, summaryData] = await Promise.all([
          insuranceApi.getCarriers(),
          insuranceApi.getClaims(),
          insuranceApi.getPreAuthorizations(),
          insuranceApi.getSumm