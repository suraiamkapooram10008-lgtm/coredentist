// ============================================
// Automations Settings Tab
// Configure n8n webhooks for workflow automation
// ============================================

import { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Calendar,
  CalendarCheck,
  CalendarPlus,
  CalendarX,
  Bell,
  CheckCircle,
  UserPlus,
  UserX,
  FileCheck,
  FileText,
  CreditCard,
  BarChart3,
  Plus,
  Trash2,
  TestTube,
  Loader2,
  Zap,
  ExternalLink,
  Shield,
  CalendarClock,
  ShieldAlert,
  PackageX,
  Star,
} from 'lucide-react';
import { automationApi } from '@/services/automationApi';
import { ConfirmationDialog } from './ConfirmationDialog';
import type { AutomationWebhook, AutomationEvent, automationEventConfigs } from '@/types/automation';
import { automationEventConfigs as eventConfigs } from '@/types/automation';

const eventIcons: Record<string, React.ReactNode> = {
  'calendar-plus': <CalendarPlus className="h-4 w-4" />,
  'calendar-check': <CalendarCheck className="h-4 w-4" />,
  'calendar-x': <CalendarX className="h-4 w-4" />,
  'calendar-clock': <CalendarClock className="h-4 w-4" />,
  'bell': <Bell className="h-4 w-4" />,
  'check-circle': <CheckCircle className="h-4 w-4" />,
  'user-plus': <UserPlus className="h-4 w-4" />,
  'user-x': <UserX className="h-4 w-4" />,
  'file-check': <FileCheck className="h-4 w-4" />,
  'file-text': <FileText className="h-4 w-4" />,
  'credit-card': <CreditCard className="h-4 w-4" />,
  'bar-chart': <BarChart3 className="h-4 w-4" />,
  'shield-alert': <ShieldAlert className="h-4 w-4" />,
  'package-x': <PackageX className="h-4 w-4" />,
  'star': <Star className="h-4 w-4" />,
};

const categoryColors: Record<string, string> = {
  appointment: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200',
  patient: 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200',
  billing: 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200',
  reports: 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200',
  inventory: 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200',
  engagement: 'bg-pink-100 text-pink-800 dark:bg-pink-900/50 dark:text-pink-200',
};

export function AutomationsTab() {
  const { toast } = useToast();
  const [webhooks, setWebhooks] = useState<AutomationWebhook[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<AutomationWebhook | null>(null);
  const [deleteWebhook, setDeleteWebhook] = useState<AutomationWebhook | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    event: '' as AutomationEvent | '',
    webhookUrl: '',
    secretToken: '',
  });

  const loadWebhooks = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await automationApi.getWebhooks();
      setWebhooks(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load automations',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadWebhooks();
  }, [loadWebhooks]);

  const handleOpenDialog = (webhook?: AutomationWebhook) => {
    if (webhook) {
      setEditingWebhook(webhook);
      setFormData({
        name: webhook.name,
        event: webhook.event,
        webhookUrl: webhook.webhookUrl,
        secretToken: webhook.secretToken || '',
      });
    } else {
      setEditingWebhook(null);
      setFormData({
        name: '',
        event: '',
        webhookUrl: '',
        secretToken: '',
      });
    }
    setIsDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formData.name || !formData.event || !formData.webhookUrl) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsSaving(true);
      if (editingWebhook) {
        const updated = await automationApi.updateWebhook(editingWebhook.id, {
          name: formData.name,
          event: formData.event as AutomationEvent,
          webhookUrl: formData.webhookUrl,
          secretToken: formData.secretToken || undefined,
        });
        setWebhooks((prev) =>
          prev.map((w) => (w.id === updated.id ? updated : w))
        );
        toast({
          title: 'Automation Updated',
          description: 'Webhook configuration has been updated',
        });
      } else {
        const created = await automationApi.createWebhook({
          name: formData.name,
          event: formData.event as AutomationEvent,
          webhookUrl: formData.webhookUrl,
          secretToken: formData.secretToken || undefined,
          isActive: false,
        });
        setWebhooks((prev) => [...prev, created]);
        toast({
          title: 'Automation Created',
          description: 'New webhook has been configured',
        });
      }
      setIsDialogOpen(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save automation',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggle = async (webhook: AutomationWebhook) => {
    if (!webhook.webhookUrl && !webhook.isActive) {
      toast({
        title: 'Configuration Required',
        description: 'Please configure the webhook URL first',
        variant: 'destructive',
      });
      return;
    }

    try {
      const updated = await automationApi.toggleWebhook(webhook.id);
      setWebhooks((prev) =>
        prev.map((w) => (w.id === updated.id ? updated : w))
      );
      toast({
        title: updated.isActive ? 'Automation Enabled' : 'Automation Disabled',
        description: `${webhook.name} is now ${updated.isActive ? 'active' : 'inactive'}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to toggle automation',
        variant: 'destructive',
      });
    }
  };

  const handleTest = async (webhook: AutomationWebhook) => {
    if (!webhook.webhookUrl) {
      toast({
        title: 'No Webhook URL',
        description: 'Please configure the webhook URL first',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsTesting(webhook.id);
      const success = await automationApi.testWebhook(
        webhook.webhookUrl,
        webhook.secretToken
      );
      toast({
        title: 'Test Sent',
        description: 'Test payload sent to webhook. Check your n8n workflow history.',
      });
    } catch (error) {
      toast({
        title: 'Test Failed',
        description: 'Failed to send test payload',
        variant: 'destructive',
      });
    } finally {
      setIsTesting(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteWebhook) return;

    try {
      await automationApi.deleteWebhook(deleteWebhook.id);
      setWebhooks((prev) => prev.filter((w) => w.id !== deleteWebhook.id));
      toast({
        title: 'Automation Deleted',
        description: 'Webhook configuration has been removed',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete automation',
        variant: 'destructive',
      });
    } finally {
      setDeleteWebhook(null);
    }
  };

  const getEventConfig = (event: AutomationEvent) => {
    return eventConfigs.find((e) => e.event === event);
  };

  const groupedWebhooks = webhooks.reduce((acc, webhook) => {
    const config = getEventConfig(webhook.event);
    const category = config?.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(webhook);
    return acc;
  }, {} as Record<string, AutomationWebhook[]>);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Workflow Automations</h3>
          <p className="text-sm text-muted-foreground">
            Connect n8n webhooks to automate notifications and workflows
          </p>
        </div>
        <Button onClick={() => handleOpenDialog()}>
          <Plus className="h-4 w-4 mr-2" />
          Add Automation
        </Button>
      </div>

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20">
        <CardContent className="flex gap-4 py-4">
          <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Powered by n8n Workflows
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Create workflows in n8n to send SMS, WhatsApp, emails, update CRMs, and more.
              Each automation triggers your n8n webhook when the event occurs.
            </p>
            <a
              href="https://n8n.io/workflows"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline dark:text-blue-400"
            >
              Browse n8n workflow templates
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Webhooks List */}
      {webhooks.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Zap className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h4 className="text-lg font-medium">No automations configured</h4>
            <p className="text-sm text-muted-foreground mt-1 mb-4">
              Add your first automation to connect n8n workflows
            </p>
            <Button onClick={() => handleOpenDialog()}>
              <Plus className="h-4 w-4 mr-2" />
              Add Automation
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {['appointment', 'patient', 'billing', 'reports', 'inventory', 'engagement'].map((category) => {
            const categoryWebhooks = groupedWebhooks[category];
            if (!categoryWebhooks?.length) return null;

            return (
              <div key={category}>
                <h4 className="text-sm font-medium text-muted-foreground mb-3 capitalize">
                  {category} Automations
                </h4>
                <div className="space-y-3">
                  {categoryWebhooks.map((webhook) => {
                    const config = getEventConfig(webhook.event);
                    return (
                      <Card key={webhook.id}>
                        <CardContent className="flex items-center gap-4 py-4">
                          {/* Icon */}
                          <div
                            className={`p-2 rounded-lg ${categoryColors[category]}`}
                          >
                            {config && eventIcons[config.icon]}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h5 className="font-medium truncate">
                                {webhook.name}
                              </h5>
                              {webhook.secretToken && (
                                <Shield className="h-3.5 w-3.5 text-green-600" />
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground truncate">
                              {config?.description || webhook.event}
                            </p>
                            {webhook.lastTriggered && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Last triggered:{' '}
                                {new Date(webhook.lastTriggered).toLocaleString()}
                              </p>
                            )}
                          </div>

                          {/* Status */}
                          <Badge
                            variant={webhook.isActive ? 'default' : 'secondary'}
                            className={
                              webhook.isActive
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200'
                                : ''
                            }
                          >
                            {webhook.isActive ? 'Active' : 'Inactive'}
                          </Badge>

                          {/* Actions */}
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleTest(webhook)}
                              disabled={isTesting === webhook.id}
                              title="Send test"
                            >
                              {isTesting === webhook.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <TestTube className="h-4 w-4" />
                              )}
                            </Button>
                            <Switch
                              checked={webhook.isActive}
                              onCheckedChange={() => handleToggle(webhook)}
                            />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenDialog(webhook)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setDeleteWebhook(webhook)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingWebhook ? 'Edit Automation' : 'Add Automation'}
            </DialogTitle>
            <DialogDescription>
              Configure an n8n webhook to trigger when this event occurs
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Appointment Confirmation SMS"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="event">Trigger Event *</Label>
              <Select
                value={formData.event}
                onValueChange={(value) =>
                  setFormData((prev) => ({
                    ...prev,
                    event: value as AutomationEvent,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an event" />
                </SelectTrigger>
                <SelectContent>
                  {eventConfigs.map((config) => (
                    <SelectItem key={config.event} value={config.event}>
                      <div className="flex items-center gap-2">
                        {eventIcons[config.icon]}
                        <span>{config.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {formData.event && (
                <p className="text-xs text-muted-foreground">
                  {getEventConfig(formData.event as AutomationEvent)?.description}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="webhookUrl">Webhook URL *</Label>
              <Input
                id="webhookUrl"
                placeholder="https://n8n.yourdomain.com/webhook/..."
                value={formData.webhookUrl}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, webhookUrl: e.target.value }))
                }
              />
              <p className="text-xs text-muted-foreground">
                Get this URL from your n8n Webhook node
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="secretToken">Secret Token (Optional)</Label>
              <Input
                id="secretToken"
                type="password"
                placeholder="Your secret token for authentication"
                value={formData.secretToken}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    secretToken: e.target.value,
                  }))
                }
              />
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Shield className="h-3 w-3" />
                Sent as Bearer token in Authorization header
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingWebhook ? 'Save Changes' : 'Add Automation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        open={!!deleteWebhook}
        onOpenChange={(open) => !open && setDeleteWebhook(null)}
        title="Delete Automation"
        description={`Are you sure you want to delete "${deleteWebhook?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        type="delete"
        onConfirm={handleDelete}
      />
    </div>
  );
}
