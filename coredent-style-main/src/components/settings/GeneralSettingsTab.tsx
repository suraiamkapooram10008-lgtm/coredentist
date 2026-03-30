// ============================================
// CoreDent PMS - General Settings Tab
// Clinic name, logo, contact, and address
// ============================================

import React, { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Loader2, Upload, Save, Building2, MapPin, Phone, Globe } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { z } from 'zod';
import type { ClinicSettings } from '@/types/clinic';
import { US_STATES } from '@/types/clinic';
import { clinicApi } from '@/services/clinicApi';

const generalSettingsSchema = z.object({
  name: z.string().trim().min(1, 'Clinic name is required').max(100),
  email: z.string().trim().email('Please enter a valid email'),
  phone: z.string().trim().min(10, 'Please enter a valid phone number'),
  fax: z.string().optional(),
  website: z.string().url('Please enter a valid URL').optional().or(z.literal('')),
  address: z.object({
    street: z.string().trim().min(1, 'Street address is required'),
    suite: z.string().optional(),
    city: z.string().trim().min(1, 'City is required'),
    state: z.string().min(2, 'State is required'),
    zipCode: z.string().regex(/^\d{5}(-\d{4})?$/, 'Please enter a valid ZIP code'),
    country: z.string().default('USA'),
  }),
});

interface GeneralSettingsTabProps {
  settings: ClinicSettings;
  onUpdate: (updates: Partial<ClinicSettings>) => void;
}

export function GeneralSettingsTab({ settings, onUpdate }: GeneralSettingsTabProps) {
  const [formData, setFormData] = useState({
    name: settings.name,
    email: settings.email,
    phone: settings.phone,
    fax: settings.fax || '',
    website: settings.website || '',
    address: { ...settings.address },
  });
  const [logoPreview, setLogoPreview] = useState<string | undefined>(settings.logoUrl);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('address.')) {
      const addressField = field.replace('address.', '');
      setFormData(prev => ({
        ...prev,
        address: { ...prev.address, [addressField]: value },
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type and size
    if (!file.type.startsWith('image/')) {
      toast({
        variant: 'destructive',
        title: 'Invalid file type',
        description: 'Please upload an image file (PNG, JPG, etc.)',
      });
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast({
        variant: 'destructive',
        title: 'File too large',
        description: 'Logo must be less than 2MB',
      });
      return;
    }

    setLogoFile(file);
    const reader = new FileReader();
    reader.onload = () => {
      setLogoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    setErrors({});

    // Validate form data
    const result = generalSettingsSchema.safeParse(formData);

    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        const path = issue.path.join('.');
        fieldErrors[path] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setIsSaving(true);

    try {
      let logoUrl = logoPreview;
      if (logoFile) {
        const uploadResponse = await clinicApi.uploadLogo(logoFile);
        if (!uploadResponse.success || !uploadResponse.data) {
          throw new Error(uploadResponse.error?.message || 'Logo upload failed');
        }
        logoUrl = uploadResponse.data.url;
      }

      const response = await clinicApi.updateSettings({ ...formData, logoUrl });
      if (!response.success || !response.data) {
        throw new Error(response.error?.message || 'Failed to save settings');
      }

      onUpdate(response.data);
      setLogoFile(null);

      toast({
        title: 'Settings Saved',
        description: 'Your clinic settings have been updated.',
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to save settings. Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Clinic Identity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Clinic Identity
          </CardTitle>
          <CardDescription>
            Your practice name and logo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Logo Upload */}
          <div className="flex items-center gap-6">
            <Avatar className="h-24 w-24">
              <AvatarImage src={logoPreview} alt="Clinic logo" />
              <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
                {formData.name?.charAt(0) || '?'}
              </AvatarFallback>
            </Avatar>
            <div className="space-y-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleLogoUpload}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="mr-2 h-4 w-4" />
                Upload Logo
              </Button>
              <p className="text-xs text-muted-foreground">
                PNG, JPG up to 2MB. Recommended: 200x200px
              </p>
            </div>
          </div>

          {/* Clinic Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Clinic Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={errors.name ? 'border-destructive' : ''}
              placeholder="Bright Smile Dental"
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Contact Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5" />
            Contact Information
          </CardTitle>
          <CardDescription>
            How patients can reach your practice
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className={errors.email ? 'border-destructive' : ''}
                placeholder="info@clinic.com"
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone *</Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                className={errors.phone ? 'border-destructive' : ''}
                placeholder="(555) 123-4567"
              />
              {errors.phone && (
                <p className="text-sm text-destructive">{errors.phone}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="fax">Fax</Label>
              <Input
                id="fax"
                type="tel"
                value={formData.fax}
                onChange={(e) => handleInputChange('fax', e.target.value)}
                placeholder="(555) 123-4568"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                type="url"
                value={formData.website}
                onChange={(e) => handleInputChange('website', e.target.value)}
                className={errors.website ? 'border-destructive' : ''}
                placeholder="https://yourpractice.com"
              />
              {errors.website && (
                <p className="text-sm text-destructive">{errors.website}</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Address */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Practice Address
          </CardTitle>
          <CardDescription>
            Your clinic's physical location
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="street">Street Address *</Label>
                <Input
                  id="street"
                  value={formData.address.street}
                  onChange={(e) => handleInputChange('address.street', e.target.value)}
                  className={errors['address.street'] ? 'border-destructive' : ''}
                  placeholder="123 Main Street"
                />
                {errors['address.street'] && (
                  <p className="text-sm text-destructive">{errors['address.street']}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="suite">Suite / Unit</Label>
                <Input
                  id="suite"
                  value={formData.address.suite}
                  onChange={(e) => handleInputChange('address.suite', e.target.value)}
                  placeholder="Suite 200"
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  value={formData.address.city}
                  onChange={(e) => handleInputChange('address.city', e.target.value)}
                  className={errors['address.city'] ? 'border-destructive' : ''}
                  placeholder="Los Angeles"
                />
                {errors['address.city'] && (
                  <p className="text-sm text-destructive">{errors['address.city']}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="state">State *</Label>
                <Select
                  value={formData.address.state}
                  onValueChange={(value) => handleInputChange('address.state', value)}
                >
                  <SelectTrigger className={errors['address.state'] ? 'border-destructive' : ''}>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    {US_STATES.map((state) => (
                      <SelectItem key={state.code} value={state.code}>
                        {state.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors['address.state'] && (
                  <p className="text-sm text-destructive">{errors['address.state']}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="zipCode">ZIP Code *</Label>
                <Input
                  id="zipCode"
                  value={formData.address.zipCode}
                  onChange={(e) => handleInputChange('address.zipCode', e.target.value)}
                  className={errors['address.zipCode'] ? 'border-destructive' : ''}
                  placeholder="90001"
                />
                {errors['address.zipCode'] && (
                  <p className="text-sm text-destructive">{errors['address.zipCode']}</p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving} size="lg" className="gap-2">
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
