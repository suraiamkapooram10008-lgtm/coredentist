/**
 * Online Booking Page
 * Patient self-scheduling and waitlist management
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
  Calendar, 
  Clock, 
  User,
  CheckCircle,
  Users,
  Send,
  Settings,
  Link,
  Copy
} from "lucide-react";

export default function OnlineBooking() {
  const [searchTerm, setSearchTerm] = useState("");
  const [bookingLink] = useState("https://coredent.app/book/abc123");

  const bookings = [
    { id: "1", patient: "John Smith", requestedDate: "Feb 20, 2026", type: "Checkup", status: "Pending", requestedAt: "Feb 12, 2026" },
    { id: "2", patient: "Jane Doe", requestedDate: "Feb 18, 2026", type: "Cleaning", status: "Approved", requestedAt: "Feb 10, 2026" },
    { id: "3", patient: "Bob Johnson", requestedDate: "Feb 25, 2026", type: "Consultation", status: "Pending", requestedAt: "Feb 11, 2026" },
  ];

  const waitlist = [
    { id: "1", patient: "Mary Wilson", type: "Cleaning", position: 1, addedDate: "Feb 8, 2026" },
    { id: "2", patient: "Tom Davis", type: "Checkup", position: 2, addedDate: "Feb 9, 2026" },
    { id: "3", patient: "Sarah Brown", type: "Whitening", position: 3, addedDate: "Feb 10, 2026" },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Approved": return "bg-green-500";
      case "Pending": return "bg-yellow-500";
      case "Rejected": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Online Booking</h1>
          <p className="text-muted-foreground">Patient self-scheduling and waitlist management</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
          <Button>
            <Send className="mr-2 h-4 w-4" />
            Send Link
          </Button>
        </div>
      </div>

      {/* Booking Link Card */}
      <Card className="bg-primary text-primary-foreground">
        <CardHeader>
          <CardTitle className="text-lg">Patient Booking Link</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input 
              value={bookingLink} 
              readOnly 
              className="bg-primary-foreground text-primary"
            />
            <Button variant="secondary">
              <Copy className="mr-2 h-4 w-4" />
              Copy
            </Button>
          </div>
          <p className="text-sm mt-2 opacity-80">Share this link with patients to allow them to book appointments online</p>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Requests</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">5</div>
            <p className="text-xs text-muted-foreground">awaiting review</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">12</div>
            <p className="text-xs text-muted-foreground">this week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Waitlist</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-xs text-muted-foreground">patients waiting</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online Bookings</CardTitle>
            <Calendar className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">28</div>
            <p className="text-xs text-muted-foreground">this month</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search bookings..." 
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="requests" className="space-y-4">
        <TabsList>
          <TabsTrigger value="requests">Booking Requests</TabsTrigger>
          <TabsTrigger value="waitlist">Waitlist</TabsTrigger>
          <TabsTrigger value="settings">Booking Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="requests">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Patient</TableHead>
                    <TableHead>Requested Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Requested At</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bookings.map((booking) => (
                    <TableRow key={booking.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          {booking.patient}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          {booking.requestedDate}
                        </div>
                      </TableCell>
                      <TableCell><Badge variant="outline">{booking.type}</Badge></TableCell>
                      <TableCell>{booking.requestedAt}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(booking.status)}>
                          {booking.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {booking.status === "Pending" && (
                            <>
                              <Button size="sm" variant="outline">Approve</Button>
                              <Button size="sm" variant="outline">Reject</Button>
                            </>
                          )}
                          <Button size="sm" variant="ghost">Message</Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="waitlist">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Waitlist Management</CardTitle>
                <Button variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Add to Waitlist
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Position</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Requested Type</TableHead>
                    <TableHead>Added Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {waitlist.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Badge variant="outline">#{item.position}</Badge>
                      </TableCell>
                      <TableCell className="font-medium">{item.patient}</TableCell>
                      <TableCell><Badge variant="outline">{item.type}</Badge></TableCell>
                      <TableCell>{item.addedDate}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline">Schedule</Button>
                          <Button size="sm" variant="ghost">Remove</Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Online Booking Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Enable Online Booking</p>
                  <p className="text-sm text-muted-foreground">Allow patients to book appointments online</p>
                </div>
                <Button variant="outline">Enabled</Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Require Approval</p>
                  <p className="text-sm text-muted-foreground">New bookings require staff approval</p>
                </div>
                <Button variant="outline">Enabled</Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Available Appointment Types</p>
                  <p className="text-sm text-muted-foreground">Configure which types patients can book</p>
                </div>
                <Button variant="outline">Configure</Button>
              </div>
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Booking Window</p>
                  <p className="text-sm text-muted-foreground">How far in advance patients can book</p>
                </div>
                <Button variant="outline">90 days</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
