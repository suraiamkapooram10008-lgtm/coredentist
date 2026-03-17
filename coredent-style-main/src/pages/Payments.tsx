/**
 * Payments Page
 * Credit card processing, recurring billing, payment terminals
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Settings
} from "lucide-react";

export default function Payments() {
  const [searchTerm, setSearchTerm] = useState("");

  const transactions = [
    { id: "1", patient: "John Smith", amount: 250.00, type: "Payment", method: "Visa ****4242", status: "Completed", date: "Feb 12, 2026" },
    { id: "2", patient: "Jane Doe", amount: 150.00, type: "Payment", method: "Mastercard ****5555", status: "Completed", date: "Feb 11, 2026" },
    { id: "3", patient: "Bob Johnson", amount: 85.00, type: "Refund", method: "Visa ****4242", status: "Completed", date: "Feb 10, 2026" },
    { id: "4", patient: "Mary Wilson", amount: 500.00, type: "Recurring", method: "Amex ****1234", status: "Pending", date: "Feb 15, 2026" },
  ];

  const recurringPlans = [
    { id: "1", patient: "Mary Wilson", plan: "Monthly Payment", amount: 500.00, frequency: "Monthly", nextDate: "Feb 15, 2026", status: "Active" },
    { id: "2", patient: "John Smith", plan: "Treatment Plan", amount: 250.00, frequency: "Bi-weekly", nextDate: "Feb 20, 2026", status: "Active" },
    { id: "3", patient: "Jane Doe", plan: "Membership Plan", amount: 49.00, frequency: "Monthly", nextDate: "Mar 1, 2026", status: "Active" },
  ];

  const terminals = [
    { id: "1", name: "Front Desk Terminal", location: "Reception", status: "Online", lastTransaction: "10 mins ago" },
    { id: "2", name: "Operatory 1", location: "Room 1", status: "Online", lastTransaction: "25 mins ago" },
    { id: "3", name: "Operatory 2", location: "Room 2", status: "Offline", lastTransaction: "2 hours ago" },
  ];

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
            <div className="text-2xl font-bold text-green-500">$2,450</div>
            <p className="text-xs text-muted-foreground">12 transactions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$28,500</div>
            <p className="text-xs text-muted-foreground">+12% from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Payments</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">$1,250</div>
            <p className="text-xs text-muted-foreground">3 pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recurring Revenue</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">$5,840</div>
            <p className="text-xs text-muted-foreground">monthly recurring</p>
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
                      <TableCell>${txn.amount.toFixed(2)}</TableCell>
                      <TableCell><Badge variant="outline">{txn.type}</Badge></TableCell>
                      <TableCell className="text-muted-foreground">{txn.method}</TableCell>
                      <TableCell>
                        <Badge className={txn.status === 'Completed' ? 'bg-green-500' : 'bg-yellow-500'}>
                          {txn.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{txn.date}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
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
                      <TableCell>${plan.amount.toFixed(2)}</TableCell>
                      <TableCell><Badge variant="outline">{plan.frequency}</Badge></TableCell>
                      <TableCell>{plan.nextDate}</TableCell>
                      <TableCell>
                        <Badge className="bg-green-500">{plan.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="terminals">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {terminals.map((terminal) => (
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
            ))}
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
                  <p className="font-medium">Payment Processor</p>
                  <p className="text-sm text-muted-foreground">Stripe integration</p>
                </div>
                <Button variant="outline">
                  <Settings className="mr-2 h-4 w-4" />
                  Configure
                </Button>
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
    </div>
  );
}
