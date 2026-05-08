/**
 * Inventory Management Page
 * Supply tracking, reorder alerts
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
  AlertTriangle, 
  Package, 
  TrendingDown, 
  TrendingUp,
  Building2,
  FileText
} from "lucide-react";
import { inventoryApi } from "@/services/inventoryApi";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";

export default function Inventory() {
  const [searchTerm, setSearchTerm] = useState("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: rulesData } = useQuery({
    queryKey: ['reorder-rules'],
    queryFn: () => inventoryApi.listRules(),
  });

  const { data: suppliersData } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => inventoryApi.listSuppliers(),
  });

  const checkMut = useMutation({
    mutationFn: () => inventoryApi.triggerReorderCheck(),
    onSuccess: (data) => {
      toast({ 
        title: "Reorder Check Complete", 
        description: `Created ${data.alerts_created} alerts and ${data.purchase_orders_created} POs.`
      });
      queryClient.invalidateQueries({ queryKey: ['inventory-items'] });
      queryClient.invalidateQueries({ queryKey: ['reorder-rules'] });
    }
  });

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Inventory Management</h1>
          <p className="text-muted-foreground">Track supplies and manage reorder alerts</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Item
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Items</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">248</div>
            <p className="text-xs text-muted-foreground">in inventory</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">12</div>
            <p className="text-xs text-muted-foreground">items need reorder</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Stock</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">236</div>
            <p className="text-xs text-muted-foreground">items available</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">5</div>
            <p className="text-xs text-muted-foreground">pending alerts</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search by name or SKU..." 
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Items</TabsTrigger>
          <TabsTrigger value="low-stock">Low Stock</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="vendors">Vendors & Contracts</TabsTrigger>
          <TabsTrigger value="rules">Reorder Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Name</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Min Qty</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Disposable Gloves (Medium)</TableCell>
                    <TableCell>GLV-001-M</TableCell>
                    <TableCell><Badge variant="outline">Supplies</Badge></TableCell>
                    <TableCell>150</TableCell>
                    <TableCell>50</TableCell>
                    <TableCell><Badge className="bg-green-500">In Stock</Badge></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Dental Mirror</TableCell>
                    <TableCell>DMR-001</TableCell>
                    <TableCell><Badge variant="outline">Equipment</Badge></TableCell>
                    <TableCell>25</TableCell>
                    <TableCell>30</TableCell>
                    <TableCell><Badge className="bg-red-500">Low Stock</Badge></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="low-stock">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Name</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Current Qty</TableHead>
                    <TableHead>Min Qty</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Dental Mirror</TableCell>
                    <TableCell>DMR-001</TableCell>
                    <TableCell>25</TableCell>
                    <TableCell>30</TableCell>
                    <TableCell><Button size="sm">Reorder</Button></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardContent className="p-6">
              <div className="text-center text-muted-foreground">
                No pending alerts
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Vendors Tab */}
        <TabsContent value="vendors">
          <Card>
            <CardHeader className="flex flex-row justify-between items-center">
              <div>
                <CardTitle>Vendors</CardTitle>
                <p className="text-sm text-muted-foreground">Manage your suppliers and contracts</p>
              </div>
              <Button size="sm"><Plus className="h-4 w-4 mr-2"/> Add Vendor</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Supplier Name</TableHead>
                    <TableHead>Contact Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {suppliersData?.suppliers?.map((s: any) => (
                    <TableRow key={s.id}>
                      <TableCell className="font-medium flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-slate-400" />
                        {s.name}
                      </TableCell>
                      <TableCell>{s.contact_name || '-'}</TableCell>
                      <TableCell>{s.email || '-'}</TableCell>
                      <TableCell><Badge variant="outline">{s.is_active ? 'Active' : 'Inactive'}</Badge></TableCell>
                    </TableRow>
                  ))}
                  {!suppliersData?.suppliers?.length && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-4 text-muted-foreground">No suppliers found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rules Tab */}
        <TabsContent value="rules">
          <Card>
            <CardHeader className="flex flex-row justify-between items-center">
              <div>
                <CardTitle>Reorder Rules</CardTitle>
                <p className="text-sm text-muted-foreground">Automated inventory replenishment rules</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => checkMut.mutate()} disabled={checkMut.isPending}>
                  Run Reorder Check
                </Button>
                <Button size="sm"><Plus className="h-4 w-4 mr-2"/> Add Rule</Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item ID</TableHead>
                    <TableHead>Trigger Qty</TableHead>
                    <TableHead>Reorder Qty</TableHead>
                    <TableHead>Auto Approve</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rulesData?.rules?.map((r: any) => (
                    <TableRow key={r.id}>
                      <TableCell className="font-medium">{r.item_id}</TableCell>
                      <TableCell>{r.trigger_quantity}</TableCell>
                      <TableCell>{r.reorder_quantity}</TableCell>
                      <TableCell>{r.auto_approve ? <Badge className="bg-green-500">Yes</Badge> : <Badge variant="secondary">No</Badge>}</TableCell>
                      <TableCell><Badge variant="outline">{r.is_active ? 'Active' : 'Disabled'}</Badge></TableCell>
                    </TableRow>
                  ))}
                  {!rulesData?.rules?.length && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-4 text-muted-foreground">No reorder rules configured.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
