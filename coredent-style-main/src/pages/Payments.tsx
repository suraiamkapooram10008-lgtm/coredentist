/**
 * Payments Page
 * Credit card processing, recurring billing, payment terminals
 * Supports: Stripe (US) and Razorpay (India - UPI/Paytm/PhonePe)
 */

import { useState, useEffect, useCallback } from "react";
import { logger } from "@/lib/logger";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  Search, 
  Plus, 
  CreditCard, 
  DollarSign, 
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Terminal,
  Settings,
  Smartphone,
  Loader2
} from "lucide-react";
import { 
  createRazorpayOrder, 
  verifyRazorpayPayment, 
  loadRazorpayScript,
  type RazorpayOrderCreate,
  type RazorpayPaymentVerify 
} from "@/services/paymentApi";
import { useToast } from "@/hooks/use-toast";
import {
  usePaymentStats,
  useTransactions,
  useRecurringPlans,
  useTerminals,
} from "@/hooks/usePayments";

// Razorpay response type
interface RazorpayResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

// Razorpay window type
interface RazorpayWindow extends Window {
  Razorpay: new (options: Record<string, unknown>) => { open: () => void };
}

export default function Payments() {
  const [searchTerm, setSearchTerm] = useState("");
  const [showRazorpayDialog, setShowRazorpayDialog] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [patientName, setPatientName] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();

  // Fetch data from API using React Query hooks
  const { data: statsData, isLoading: statsLoading } = usePaymentStats();
  const { data: transactionsData, isLoading: transactionsLoading } = useTransactions({ search: searchTerm || undefined });
  const { data: recurringData, isLoading: recurringLoading } = useRecurringPlans();
  const { data: terminalsData, isLoading: terminalsLoading } = useTerminals();

  const stats = statsData?.data;
  const transactions = transactionsData?.data?.transactions ?? [];
  const recurringPlans = recurringData?.data?.plans ?? [];
  const terminals = terminalsData?.data?.terminals ?? [];

  // Load Razorpay SDK on mount
  useEffect(() => {
    let cancelled = false;
    loadRazorpayScript().then((success) => {
      if (!cancelled && !success) {
        logger.warn("Failed to load Razorpay SDK - UPI payments may not work");
      }
    });
    return () => { cancelled = true; };
  }, []);

  // Handle Razorpay payment
  const handleRazorpayPayment = useCallback(async () => {
    if (!paymentAmount || !patientName) {
      toast({
        title: "Missing Information",
        description: "Please enter patient name and amount",
        variant: "destructive",
      });
      return;
    }

    setIsProcessing(true);

    try {
      // Step 1: Create order
      const orderData: RazorpayOrderCreate = {
        invoice_id: crypto.randomUUID(), // In production, use actual invoice_id
        amount: parseFloat(paymentAmount),
        currency: "INR",
        receipt: `receipt_${Date.now()}`,
      };

      const orderResponse = await createRazorpayOrder(orderData);
      const order = orderResponse.data;

      if (!order) {
        toast({
          title: "Order Creation Failed",
          description: "Failed to create payment order. Please try again.",
          variant: "destructive",
        });
        setIsProcessing(false);
        return;
      }

      // Step 2: Open Razorpay checkout
      const razorpayWindow = window as unknown as RazorpayWindow;
      if (typeof window !== "undefined" && razorpayWindow.Razorpay) {
        const options: Record<string, unknown> = {
          key: order.key_id,
          amount: order.amount,
          currency: order.currency,
          name: "CoreDent PMS",
          description: `Payment for ${patientName}`,
          order_id: order.order_id,
          handler: async (response: RazorpayResponse) => {
            // Step 3: Verify payment
            const verifyData: RazorpayPaymentVerify = {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              invoice_id: orderData.invoice_id,
            };

            try {
              const verifyResponse = await verifyRazorpayPayment(verifyData);
              const paymentId = verifyResponse.data?.payment_id || "Unknown";
              toast({
                title: "Payment Successful!",
                description: `Payment ID: ${paymentId}`,
              });
              setShowRazorpayDialog(false);
              setPaymentAmount("");
              setPatientName("");
            } catch (error) {
              logger.error("Payment verification failed", error instanceof Error ? error : undefined);
              toast({
                title: "Verification Failed",
                description: "Payment was made but verification failed. Contact support.",
                variant: "destructive",
              });
            }
          },
          prefill: {
            name: patientName,
          },
          theme: {
            color: "#0ea5e9",
          },
          modal: {
            ondismiss: () => {
              setIsProcessing(false);
            },
          },
        };

        const razorpay = new razorpayWindow.Razorpay(options);
        razorpay.open();
      } else {
        toast({
          title: "Payment Gateway UNAVAILABLE",
          description: "Razorpay SDK not loaded. Please refresh the page.",
          variant: "destructive",
        });
      }
    } catch (error: unknown) {
      const detail = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to create payment order";
      logger.error("Razorpay payment failed", error instanceof Error ? error : undefined, { detail });
      toast({
        title: "Payment Failed",
        description: detail || "Failed to create payment order",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  }, [paymentAmount, patientName, toast]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatUSD = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Payments</h1>
          <p className="text-muted-foreground">Credit card processing and billing</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Terminal className="mr-2 h-4 w-4" />
            Terminals
          </Button>
          <Button onClick={() => setShowRazorpayDialog(true)}>
            <Smartphone className="mr-2 h-4 w-4" />
            Pay with UPI
          </Button>
          <Button>
            <CreditCard className="mr-2 h-4 w-4" />
            Process Payment
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-2xl font-bold text-green-500">
                  {formatUSD(stats?.todayRevenue ?? 0)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.todayTransactions ?? 0} transactions
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {formatUSD(stats?.monthRevenue ?? 0)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.monthGrowth ? `+${stats.monthGrowth}% from last month` : 'No data'}
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Payments</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-2xl font-bold text-yellow-500">
                  {formatUSD(stats?.pendingPayments ?? 0)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats?.pendingCount ?? 0} pending
                </p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recurring Revenue</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            ) : (
              <>
                <div className="text-2xl font-bold text-blue-500">
                  {formatUSD(stats?.recurringRevenue ?? 0)}
                </div>
                <p className="text-xs text-muted-foreground">monthly recurring</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="transactions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="recurring">Recurring Billing</TabsTrigger>
          <TabsTrigger value="terminals">Terminals</TabsTrigger>
          <TabsTrigger value="settings">Payment Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="transactions">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Recent Transactions</CardTitle>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input 
                    placeholder="Search transactions..." 
                    className="pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {transactionsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : transactions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No transactions found
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Patient</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Payment Method</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((txn) => (
                      <TableRow key={txn.id}>
                        <TableCell className="font-medium">{txn.patient}</TableCell>
                        <TableCell>{formatUSD(txn.amount)}</TableCell>
                        <TableCell><Badge variant="outline">{txn.type}</Badge></TableCell>
                        <TableCell className="text-muted-foreground">{txn.method}</TableCell>
                        <TableCell>
                          <Badge className={txn.status === 'Completed' ? 'bg-green-500' : txn.status === 'Failed' ? 'bg-red-500' : 'bg-yellow-500'}>
                            {txn.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{txn.date}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recurring">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Recurring Billing Plans</CardTitle>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Plan
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {recurringLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : recurringPlans.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No recurring billing plans found
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Patient</TableHead>
                      <TableHead>Plan</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Frequency</TableHead>
                      <TableHead>Next Date</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recurringPlans.map((plan) => (
                      <TableRow key={plan.id}>
                        <TableCell className="font-medium">{plan.patient}</TableCell>
                        <TableCell>{plan.plan}</TableCell>
                        <TableCell>{formatUSD(plan.amount)}</TableCell>
                        <TableCell><Badge variant="outline">{plan.frequency}</Badge></TableCell>
                        <TableCell>{plan.nextDate}</TableCell>
                        <TableCell>
                          <Badge className={plan.status === 'Active' ? 'bg-green-500' : plan.status === 'Cancelled' ? 'bg-red-500' : 'bg-yellow-500'}>
                            {plan.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="terminals">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {terminalsLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <div className="h-6 w-32 animate-pulse rounded bg-muted" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                    <div className="h-4 w-32 animate-pulse rounded bg-muted mt-2" />
                  </CardContent>
                </Card>
              ))
            ) : terminals.length === 0 ? (
              <div className="col-span-3 text-center py-8 text-muted-foreground">
                No payment terminals found
              </div>
            ) : (
              terminals.map((terminal) => (
                <Card key={terminal.id}>
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-lg">{terminal.name}</CardTitle>
                      <Badge className={terminal.status === 'Online' ? 'bg-green-500' : 'bg-red-500'}>
                        {terminal.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{terminal.location}</p>
                    <p className="text-sm text-muted-foreground mt-1">Last: {terminal.lastTransaction}</p>
                    <div className="mt-4 flex gap-2">
                      <Button size="sm" variant="outline">Test</Button>
                      <Button size="sm" variant="outline">Settings</Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Payment Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">US Payment Processor</p>
                  <p className="text-sm text-muted-foreground">Stripe - Credit/Debit cards</p>
                </div>
                <Button variant="outline">
                  <Settings className="mr-2 h-4 w-4" />
                  Configure
                </Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">India Payment Processor</p>
                  <p className="text-sm text-muted-foreground">Razorpay - UPI, Paytm, PhonePe, Cards, Net Banking</p>
                </div>
                <Badge className="bg-green-500">Active</Badge>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Accept Credit Cards</p>
                  <p className="text-sm text-muted-foreground">Visa, Mastercard, Amex, Discover</p>
                </div>
                <Button variant="outline">Enable</Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Recurring Payments</p>
                  <p className="text-sm text-muted-foreground">Setup automatic billing</p>
                </div>
                <Button variant="outline">Enable</Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Payment Receipts</p>
                  <p className="text-sm text-muted-foreground">Email receipts automatically</p>
                </div>
                <Button variant="outline">Configure</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Razorpay Payment Dialog */}
      <Dialog open={showRazorpayDialog} onOpenChange={setShowRazorpayDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Pay with UPI / Indian Payment Methods</DialogTitle>
            <DialogDescription>
              Accept payments via UPI (GPay, PhonePe, Paytm), Cards, Net Banking, or Wallets
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="patient-name">Patient Name</Label>
              <Input
                id="patient-name"
                placeholder="Enter patient name"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (₹)</Label>
              <Input
                id="amount"
                type="number"
                placeholder="Enter amount in INR"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
              />
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm font-medium mb-2">Accepted Payment Methods:</p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary" className="gap-1">
                  <Smartphone className="h-3 w-3" /> UPI (GPay, PhonePe, Paytm)
                </Badge>
                <Badge variant="secondary" className="gap-1">
                  <CreditCard className="h-3 w-3" /> Cards (Visa, MC, RuPay)
                </Badge>
                <Badge variant="secondary">Net Banking</Badge>
                <Badge variant="secondary">Wallets</Badge>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRazorpayDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleRazorpayPayment} 
              disabled={isProcessing || !paymentAmount || !patientName}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Smartphone className="mr-2 h-4 w-4" />
                  Pay Now
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}