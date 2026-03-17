/**
 * Referral Management Page
 * Patient referrals and specialist communication
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
  UserPlus, 
  Clock, 
  CheckCircle, 
  XCircle,
  DollarSign,
  TrendingUp
} from "lucide-react";

export default function Referrals() {
  const [searchTerm, setSearchTerm] = useState("");

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Referral Management</h1>
          <p className="text-muted-foreground">Track patient referrals and specialist communications</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Referral
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Referrals</CardTitle>
            <UserPlus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85</div>
            <p className="text-xs text-muted-foreground">this quarter</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">12</div>
            <p className="text-xs text-muted-foreground">awaiting appointment</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">68</div>
            <p className="text-xs text-muted-foreground">completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Referral Fees</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$2,450</div>
            <p className="text-xs text-muted-foreground">collected</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search referrals by patient or case number..." 
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Referrals</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Specialist</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Fee</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>Feb 10, 2026</TableCell>
                    <TableCell className="font-medium">John Smith</TableCell>
                    <TableCell><Badge variant="outline">Oral Surgery</Badge></TableCell>
                    <TableCell>Dr. Wilson</TableCell>
                    <TableCell><Badge className="bg-yellow-500">Pending</Badge></TableCell>
                    <TableCell>$150.00</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Feb 8, 2026</TableCell>
                    <TableCell className="font-medium">Jane Doe</TableCell>
                    <TableCell><Badge variant="outline">Endodontics</Badge></TableCell>
                    <TableCell>Dr. Brown</TableCell>
                    <TableCell><Badge className="bg-green-500">Completed</Badge></TableCell>
                    <TableCell>$200.00</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Feb 5, 2026</TableCell>
                    <TableCell className="font-medium">Bob Johnson</TableCell>
                    <TableCell><Badge variant="outline">Periodontics</Badge></TableCell>
                    <TableCell>Dr. Green</TableCell>
                    <TableCell><Badge className="bg-blue-500">Scheduled</Badge></TableCell>
                    <TableCell>$100.00</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pending">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Specialist</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>Feb 10, 2026</TableCell>
                    <TableCell className="font-medium">John Smith</TableCell>
                    <TableCell><Badge variant="outline">Oral Surgery</Badge></TableCell>
                    <TableCell>Dr. Wilson</TableCell>
                    <TableCell><Button size="sm">Send Reminder</Button></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardContent className="p-6">
              <div className="text-center text-muted-foreground">
                View completed referrals
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sources">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Source Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Total Referrals</TableHead>
                    <TableHead>Active</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Dr. Wilson Oral Surgery</TableCell>
                    <TableCell><Badge variant="outline">Other Dentist</Badge></TableCell>
                    <TableCell>(555) 111-2222</TableCell>
                    <TableCell>45</TableCell>
                    <TableCell><Badge className="bg-green-500">Yes</Badge></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
