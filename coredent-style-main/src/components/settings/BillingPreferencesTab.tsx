// ============================================
// CoreDent PMS - Billing Preferences Tab
// Configure billing and invoicing settings
// ============================================

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Save, DollarSign, Receipt, Clock, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { z } from 'zod';
import type { BillingPreferences, PaymentMethod } from '@/types/settings';
import { paymentMethodLabels, currencyOptions } from '@/types/settings';
import { settingsApi } from '@/services/api';

const billingSchema = z.object({
  taxRate: z.number().min(0).max(100),
  taxLabel: z.string().min(1).max(50),
  defaultPaymentTerms: z.number().min(0).max(365),
  invoicePrefix: z.string().min(1).max(10),
  invoiceStartNumber: z.number().min(1),
  currency: z.string(),
  receiptFooterText: z.string().max(500),
  lateFeePercentage: z.number().min(0).max(100),
  lateFeeGracePeriod: z.number().min(0).max(365),
});

interface BillingPreferencesTabProps {
  preferences: BillingPreferences;
  onUpdate: (preferences: BillingPreferences) => void;
}

export function BillingPreferencesTab({ preferences, onUpdate }: BillingPreferencesTabProps) {
  const { toast } = useToast();
  const [formData, setFormData] = useState<BillingPreferences>(preferences);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  const handleInputChange = (field: keyof BillingPreferences, value: string | number | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handlePaymentMethodToggle = (method: PaymentMethod) => {
    setFormData(prev => {
      const current = prev.acceptedPaymentMethods;
      if (current.includes(method)) {
        // Don't allow removing all payment methods
        if (current.length === 1) {
          toast({
            title: 'Cannot remove',
            description: 'At least one payment method must be selected',
            variant: 'destructive',
          });
          return prev;
        }
        return { ...prev, acceptedPaymentMethods: current.filter(m => m !== method) };
      } else {
        return { ...prev, acceptedPaymentMethods: [...current, method] };
      }
    });
  };

  const handleSave = async () => {
    try {
      // Validate
      const validated = billingSchema.safeParse({
        taxRate: formData.taxRate,
        taxLabel: formData.taxLabel,
        defaultPaymentTerms: formData.defaultPaymentTerms,
        invoicePrefix: formData.invoicePrefix,
        invoiceStartNumber: formData.invoiceStartNumber,
        currency: formData.currency,
        receiptFooterText: formData.receiptFooterText,
        lateFeePercentage: formData.lateFeePercentage,
        lateFeeGracePeriod: formData.lateFeeGracePeriod,
      });

      if (!validated.success) {
        const fieldErrors: Record<string, string> = {};
        validated.error.errors.forEach(err => {
          if (err.path[0]) {
            fieldErrors[err.path[0] as string] = err.message;
          }
        });
        setErrors(fieldErrors);
        return;
      }

      setIsSaving(true);
      const response = await settingsApi.updateBillingPreferences(formData);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to save preferences');
      }
      onUpdate(response.data);
      toast({
        title: 'Preferences saved',
        description: 'Your billing preferences have been updated',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save preferences. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Invoice Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Receipt className="h-5 w-5" />
            Invoice Settings
          </CardTitle>
          <CardDescription>
            Configure how invoices are generated and numbered
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="invoicePrefix">Invoice Prefix</Label>
              <Input
                id="invoicePrefix"
                value={formData.invoicePrefix}
                onChange={e => handleInputChange('invoicePrefix', e.target.value)}
                placeholder="INV"
                maxLength={10}
              />
              {errors.invoicePrefix && (
                <p className="text-sm text-destructive">{errors.invoicePrefix}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Example: {formData.invoicePrefix}-{formData.invoiceStartNumber}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="invoiceStartNumber">Starting Number</Label>
              <Input
                id="invoiceStartNumber"
                type="number"
                min={1}
                value={formData.invoiceStartNumber}
                onChange={e => handleInputChange('invoiceStartNumber', parseInt(e.target.value) || 1)}
              />
              {errors.invoiceStartNumber && (
                <p className="text-sm text-destructive">{errors.invoiceStartNumber}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Select
                value={formData.currency}
                onValueChange={value => handleInputChange('currency', value)}
              >
                <SelectTrigger id="currency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {currencyOptions.map(option => (
                    <SelectItem key={option.code} value={option.code}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="defaultPaymentTerms">Default Payment Terms (days)</Label>
              <Input
                id="defaultPaymentTerms"
                type="number"
                min={0}
                max={365}
                value={formData.defaultPaymentTerms}
                onChange={e => handleInputChange('defaultPaymentTerms', parseInt(e.target.value) || 0)}
              />
              {errors.defaultPaymentTerms && (
                <p className="text-sm text-destructive">{errors.defaultPaymentTerms}</p>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-send Invoices</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically email invoices when created
                </p>
              </div>
              <Switch
                checked={formData.autoSendInvoices}
                onCheckedChange={checked => handleInputChange('autoSendInvoices', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-send Receipts</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically email receipts after payment
                </p>
              </div>
              <Switch
                checked={formData.autoSendReceipts}
                onCheckedChange={checked => handleInputChange('autoSendReceipts', checked)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="receiptFooterText">Receipt Footer Text</Label>
            <Textarea
              id="receiptFooterText"
              value={formData.receiptFooterText}
              onChange={e => handleInputChange('receiptFooterText', e.target.value)}
              placeholder="Thank you for your payment!"
              rows={2}
              maxLength={500}
            />
            <p className="text-xs text-muted-foreground">
              {formData.receiptFooterText.length}/500 characters
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Tax Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Tax Settings
          </CardTitle>
          <CardDescription>
            Configure sales tax for your invoices
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Tax</Label>
              <p className="text-sm text-muted-foreground">
                Apply tax to invoice line items
              </p>
            </div>
            <Switch
              checked={formData.enableTax}
              onCheckedChange={checked => handleInputChange('enableTax', checked)}
            />
          </div>

          {formData.enableTax && (
            <div className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="taxLabel">Tax Label</Label>
                <Input
                  id="taxLabel"
                  value={formData.taxLabel}
                  onChange={e => handleInputChange('taxLabel', e.target.value)}
                  placeholder="Sales Tax"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="taxRate">Tax Rate (%)</Label>
                <Input
                  id="taxRate"
                  type="number"
                  min={0}
                  max={100}
                  step={0.01}
                  value={formData.taxRate}
                  onChange={e => handleInputChange('taxRate', parseFloat(e.target.value) || 0)}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment Methods */}
      <Card>
        <CardHeader>
          <CardTitle>Accepted Payment Methods</CardTitle>
          <CardDescription>
            Select which payment methods your practice accepts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(Object.keys(paymentMethodLabels) as PaymentMethod[]).map(method => (
              <div key={method} className="flex items-center space-x-3">
                <Checkbox
                  id={method}
                  checked={formData.acceptedPaymentMethods.includes(method)}
                  onCheckedChange={() => handlePaymentMethodToggle(method)}
                />
                <Label htmlFor={method} className="cursor-pointer">
                  {paymentMethodLabels[method]}
                </Label>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Late Fee Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Late Fee Settings
          </CardTitle>
          <CardDescription>
            Configure automatic late fees for overdue invoices
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Late Fees</Label>
              <p className="text-sm text-muted-foreground">
                Automatically apply late fees to overdue invoices
              </p>
            </div>
            <Switch
              checked={formData.lateFeeEnabled}
              onCheckedChange={checked => handleInputChange('lateFeeEnabled', checked)}
            />
          </div>

          {formData.lateFeeEnabled && (
            <>
              <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 p-4 flex gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800 dark:text-yellow-200">
                  Late fees will be automatically calculated and added to overdue invoices 
                  after the grace period expires.
                </div>
              </div>

              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="lateFeeGracePeriod">Grace Period (days)</Label>
                  <Input
                    id="lateFeeGracePeriod"
                    type="number"
                    min={0}
                    max={365}
                    value={formData.lateFeeGracePeriod}
                    onChange={e => handleInputChange('lateFeeGracePeriod', parseInt(e.target.value) || 0)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Days after due date before late fee applies
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lateFeePercentage">Late Fee Rate (%)</Label>
                  <Input
                    id="lateFeePercentage"
                    type="number"
                    min={0}
                    max={100}
                    step={0.1}
                    value={formData.lateFeePercentage}
                    onChange={e => handleInputChange('lateFeePercentage', parseFloat(e.target.value) || 0)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Percentage of outstanding balance
                  </p>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving} className="gap-2">
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save Preferences
        </Button>
      </div>
    </div>
  );
}
