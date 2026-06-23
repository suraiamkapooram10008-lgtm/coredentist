import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { settingsApi } from '@/services/api';
import type { BillingPreferences } from '@/types/settings';
import { Loader2, Save } from 'lucide-react';

interface BillingPreferencesTabProps {
  preferences: BillingPreferences;
  onUpdate: (preferences: BillingPreferences) => void;
}

export function BillingPreferencesTab({ preferences, onUpdate }: BillingPreferencesTabProps) {
  const { toast } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState<BillingPreferences>({ ...preferences });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const res = await settingsApi.updateBillingPreferences(formData);
      if (res.success && res.data) {
        onUpdate(res.data);
        toast({
          title: 'Preferences Saved',
          description: 'Billing configurations and preferences updated successfully.',
        });
      } else {
        toast({
          title: 'Error',
          description: res.error?.message || 'Failed to update billing preferences',
          variant: 'destructive',
        });
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to update preferences due to a network issue.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="border-none shadow-[0_15px_40px_rgba(0,0,0,0.02)] rounded-3xl overflow-hidden bg-white">
      <CardHeader>
        <CardTitle className="text-xl font-black text-slate-800 tracking-tight">Billing & Invoicing Preferences</CardTitle>
        <CardDescription className="text-slate-400 font-medium">Configure taxes, late payment terms, receipt footer statements, and automatic client communications.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* General Invoicing */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="invoice-prefix" className="text-xs font-black uppercase tracking-widest text-slate-400">Invoice Prefix</Label>
              <Input
                id="invoice-prefix"
                value={formData.invoicePrefix}
                onChange={(e) => setFormData({ ...formData, invoicePrefix: e.target.value })}
                placeholder="INV"
                className="h-12 rounded-xl border-slate-200 font-bold"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invoice-start" className="text-xs font-black uppercase tracking-widest text-slate-400">Invoice Start Number</Label>
              <Input
                id="invoice-start"
                type="number"
                value={formData.invoiceStartNumber}
                onChange={(e) => setFormData({ ...formData, invoiceStartNumber: Number(e.target.value) })}
                className="h-12 rounded-xl border-slate-200 font-bold"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="payment-terms" className="text-xs font-black uppercase tracking-widest text-slate-400">Default Terms (Days)</Label>
              <Input
                id="payment-terms"
                type="number"
                value={formData.defaultPaymentTerms}
                onChange={(e) => setFormData({ ...formData, defaultPaymentTerms: Number(e.target.value) })}
                className="h-12 rounded-xl border-slate-200 font-bold"
                required
              />
            </div>
          </div>

          {/* Tax Configurations */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <div className="flex justify-between items-center">
              <div>
                <Label className="text-sm font-black text-slate-700 block">Apply Tax on Invoices</Label>
                <span className="text-xs text-slate-400 font-medium">Toggle if you are required to charge standard goods or service taxes.</span>
              </div>
              <Switch
                checked={formData.enableTax}
                onCheckedChange={(checked) => setFormData({ ...formData, enableTax: checked })}
              />
            </div>

            {formData.enableTax && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in duration-300">
                <div className="space-y-2">
                  <Label htmlFor="tax-label" className="text-xs font-black uppercase tracking-widest text-slate-400">Tax Label</Label>
                  <Input
                    id="tax-label"
                    value={formData.taxLabel}
                    onChange={(e) => setFormData({ ...formData, taxLabel: e.target.value })}
                    placeholder="e.g. GST or VAT"
                    className="h-12 rounded-xl border-slate-200 font-bold"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tax-rate" className="text-xs font-black uppercase tracking-widest text-slate-400">Tax Rate (%)</Label>
                  <Input
                    id="tax-rate"
                    type="number"
                    step="0.01"
                    value={formData.taxRate}
                    onChange={(e) => setFormData({ ...formData, taxRate: Number(e.target.value) })}
                    className="h-12 rounded-xl border-slate-200 font-bold"
                    required
                  />
                </div>
              </div>
            )}
          </div>

          {/* Late Fees */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <div className="flex justify-between items-center">
              <div>
                <Label className="text-sm font-black text-slate-700 block">Late Payment Penalty Fees</Label>
                <span className="text-xs text-slate-400 font-medium">Apply a percentage charge on overdue invoices.</span>
              </div>
              <Switch
                checked={formData.lateFeeEnabled}
                onCheckedChange={(checked) => setFormData({ ...formData, lateFeeEnabled: checked })}
              />
            </div>

            {formData.lateFeeEnabled && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in duration-300">
                <div className="space-y-2">
                  <Label htmlFor="late-rate" className="text-xs font-black uppercase tracking-widest text-slate-400">Late Fee (%)</Label>
                  <Input
                    id="late-rate"
                    type="number"
                    step="0.01"
                    value={formData.lateFeePercentage}
                    onChange={(e) => setFormData({ ...formData, lateFeePercentage: Number(e.target.value) })}
                    className="h-12 rounded-xl border-slate-200 font-bold"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="late-grace" className="text-xs font-black uppercase tracking-widest text-slate-400">Grace Period (Days)</Label>
                  <Input
                    id="late-grace"
                    type="number"
                    value={formData.lateFeeGracePeriod}
                    onChange={(e) => setFormData({ ...formData, lateFeeGracePeriod: Number(e.target.value) })}
                    className="h-12 rounded-xl border-slate-200 font-bold"
                    required
                  />
                </div>
              </div>
            )}
          </div>

          {/* Automations */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 text-[10px]">Automation Switches</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex justify-between items-center p-4 border border-slate-100 rounded-2xl bg-slate-50/20">
                <div>
                  <Label className="text-xs font-bold text-slate-700 block">Auto-Send Invoices</Label>
                  <span className="text-[10px] text-slate-400 font-medium">Email billing requests to patients instantly.</span>
                </div>
                <Switch
                  checked={formData.autoSendInvoices}
                  onCheckedChange={(checked) => setFormData({ ...formData, autoSendInvoices: checked })}
                />
              </div>
              <div className="flex justify-between items-center p-4 border border-slate-100 rounded-2xl bg-slate-50/20">
                <div>
                  <Label className="text-xs font-bold text-slate-700 block">Auto-Send Receipts</Label>
                  <span className="text-[10px] text-slate-400 font-medium">Send confirmation receipts immediately upon payment receipt.</span>
                </div>
                <Switch
                  checked={formData.autoSendReceipts}
                  onCheckedChange={(checked) => setFormData({ ...formData, autoSendReceipts: checked })}
                />
              </div>
            </div>
          </div>

          {/* Receipt Statement */}
          <div className="space-y-2 pt-4 border-t border-slate-100">
            <Label htmlFor="receipt-footer" className="text-xs font-black uppercase tracking-widest text-slate-400">Receipt Footer Text</Label>
            <Textarea
              id="receipt-footer"
              value={formData.receiptFooterText}
              onChange={(e) => setFormData({ ...formData, receiptFooterText: e.target.value })}
              placeholder="e.g. Thank you for choosing CoreDent. Please retain this receipt for tax filings."
              className="min-h-[80px] rounded-xl border-slate-200 font-medium p-4"
            />
          </div>

          <div className="flex justify-end pt-4">
            <Button
              type="submit"
              disabled={isSaving}
              className="px-8 h-12 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-black flex items-center justify-center gap-2 shadow-lg shadow-blue-100"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" /> Save Preferences
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
