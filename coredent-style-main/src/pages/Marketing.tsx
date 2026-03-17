/**
 * Marketing Page
 * Email campaigns, newsletters, patient engagement
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
  Mail, 
  Users, 
  BarChart3,
  Send,
  Clock,
  MousePointer,
  TrendingUp,
  DollarSign
} from "lucide-react";

export default function Marketing() {
  const [searchTerm, setSearchTerm] = useState("");

  const campaigns = [
    { id: "1", name: "Spring Cleaning Special", type: "Email", status: "Active", sent: 450, opens: 180, clicks: 45, date: "Feb 10, 2026" },
    { id: "2", name: "New Patient Welcome", type: "Automated", status: "Active", sent: 85, opens: 72, clicks: 28, date: "Jan 15, 2026" },
    { id: "3", name: "Recall Reminder", type: "SMS", status: "Scheduled", sent: 0, opens: 0, clicks: 0, date: "Feb 20, 2026" },
  ];

  const segments = [
    { id: "1", name: "Active Patients", count: 850, criteria: "Last visit < 12 months ago" },
    { id: "2", name: "Inactive Patients", count: 125, criteria: "Last visit > 12 months ago" },
    { id: "3", name: "New Patients (2026)", count: 45, criteria: "First visit in 2026" },
    { id: "4", name: "Insurance Patients", count: 620, criteria: "Has insurance on file" },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Marketing</h1>
          <p className="text-muted-foreground">Email campaigns, newsletters, and patient engagement</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Campaign
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Subscribers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">975</div>
            <p className="text-xs text-muted-foreground">active patients</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Campaigns Sent</CardTitle>
            <Send className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">this month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Open Rate</CardTitle>
            <MousePointer className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">42%</div>
            <p className="text-xs text-muted-foreground">industry avg: 21%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue from Campaigns</CardTitle>
            <DollarSign className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">$8,500</div>
            <p className="text-xs text-muted-foreground">tracked conversions</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="campaigns" className="space-y-4">
        <TabsList>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="segments">Patient Segments</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="campaigns">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Email Campaigns</CardTitle>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input 
                    placeholder="Search campaigns..." 
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
                    <TableHead>Campaign Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Sent</TableHead>
                    <TableHead>Opens</TableHead>
                    <TableHead>Clicks</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaigns.map((campaign) => (
                    <TableRow key={campaign.id}>
                      <TableCell className="font-medium">{campaign.name}</TableCell>
                      <TableCell><Badge variant="outline">{campaign.type}</Badge></TableCell>
                      <TableCell>
                        <Badge className={campaign.status === 'Active' ? 'bg-green-500' : campaign.status === 'Scheduled' ? 'bg-yellow-500' : 'bg-gray-500'}>
                          {campaign.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{campaign.sent.toLocaleString()}</TableCell>
                      <TableCell>{campaign.opens.toLocaleString()}</TableCell>
                      <TableCell>{campaign.clicks.toLocaleString()}</TableCell>
                      <TableCell>{campaign.date}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="segments">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {segments.map((segment) => (
              <Card key={segment.id}>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-lg">{segment.name}</CardTitle>
                    <Badge variant="outline">{segment.count} patients</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{segment.criteria}</p>
                  <div className="mt-4 flex gap-2">
                    <Button size="sm" variant="outline">Edit</Button>
                    <Button size="sm">Send Campaign</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            <Card className="border-dashed">
              <CardContent className="flex items-center justify-center h-full min-h-[150px]">
                <Button variant="ghost">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Segment
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="templates">
          <Card>
            <CardHeader>
              <CardTitle>Email Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border rounded-lg p-4 hover:shadow-md cursor-pointer transition-shadow">
                  <div className="h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                    <Mail className="h-8 w-8 text-gray-400" />
                  </div>
                  <h4 className="font-medium">Welcome Email</h4>
                  <p className="text-sm text-muted-foreground">New patient welcome series</p>
                </div>
                <div className="border rounded-lg p-4 hover:shadow-md cursor-pointer transition-shadow">
                  <div className="h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                    <Clock className="h-8 w-8 text-gray-400" />
                  </div>
                  <h4 className="font-medium">Recall Reminder</h4>
                  <p className="text-sm text-muted-foreground">6-month dental recall</p>
                </div>
                <div className="border rounded-lg p-4 hover:shadow-md cursor-pointer transition-shadow">
                  <div className="h-32 bg-gray-100 rounded mb-3 flex items-center justify-center">
                    <TrendingUp className="h-8 w-8 text-gray-400" />
                  </div>
                  <h4 className="font-medium">Special Offer</h4>
                  <p className="text-sm text-muted-foreground">Promotional campaign</p>
                </div>
              </div>
              <Button variant="outline" className="mt-4">
                <Plus className="mr-2 h-4 w-4" />
                Create Template
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Campaign Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  <BarChart3 className="h-16 w-16 opacity-20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Patient Engagement</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Email Open Rate</span>
                    <span className="font-medium">42%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Click-through Rate</span>
                    <span className="font-medium">8.5%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Conversion Rate</span>
                    <span className="font-medium">12%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Unsubscribes</span>
                    <span className="font-medium">2%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
