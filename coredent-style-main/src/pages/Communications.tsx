/**
 * Communications Page
 * Patient messaging, SMS/email reminders, two-way messaging
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
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
  MessageSquare, 
  Mail, 
  Phone, 
  Clock,
  Send,
  Inbox,
  CheckCircle,
  AlertCircle
} from "lucide-react";

export default function Communications() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);

  const conversations = [
    { id: "1", patient: "John Smith", lastMessage: "Thanks for the reminder!", time: "10:30 AM", unread: 0, channel: "SMS" },
    { id: "2", patient: "Jane Doe", lastMessage: "I'll confirm my appointment", time: "9:15 AM", unread: 1, channel: "Email" },
    { id: "3", patient: "Bob Johnson", lastMessage: "Can I reschedule?", time: "Yesterday", unread: 0, channel: "SMS" },
  ];

  const reminders = [
    { id: "1", patient: "John Smith", type: "Appointment", scheduled: "Feb 14, 2026 10:00 AM", status: "Sent" },
    { id: "2", patient: "Jane Doe", type: "Follow-up", scheduled: "Feb 15, 2026 2:00 PM", status: "Pending" },
    { id: "3", patient: "Mary Wilson", type: "Recall", scheduled: "Feb 20, 2026", status: "Pending" },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Patient Communications</h1>
          <p className="text-muted-foreground">Manage messages, reminders, and notifications</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Message
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unread Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">5</div>
            <p className="text-xs text-muted-foreground">needs attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sent Today</CardTitle>
            <Send className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">28</div>
            <p className="text-xs text-muted-foreground">messages sent</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">12</div>
            <p className="text-xs text-muted-foreground">reminders pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivery Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">98%</div>
            <p className="text-xs text-muted-foreground">successful deliveries</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="messages" className="space-y-4">
        <TabsList>
          <TabsTrigger value="messages">Messages</TabsTrigger>
          <TabsTrigger value="reminders">Reminders</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="messages">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Conversation List */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Conversations</CardTitle>
                <div className="relative mt-2">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input 
                    placeholder="Search messages..." 
                    className="pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y">
                  {conversations.map((conv) => (
                    <div 
                      key={conv.id}
                      className={`p-4 cursor-pointer hover:bg-muted/50 ${selectedConversation === conv.id ? 'bg-muted' : ''}`}
                      onClick={() => setSelectedConversation(conv.id)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{conv.patient}</p>
                          <p className="text-sm text-muted-foreground truncate">{conv.lastMessage}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">{conv.time}</p>
                          {conv.unread > 0 && (
                            <Badge className="mt-1 bg-blue-500">{conv.unread}</Badge>
                          )}
                        </div>
                      </div>
                      <div className="mt-2">
                        <Badge variant="outline" className="text-xs">
                          {conv.channel === 'SMS' ? <Phone className="h-3 w-3 mr-1" /> : <Mail className="h-3 w-3 mr-1" />}
                          {conv.channel}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Message Thread */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Conversation with John Smith</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-end">
                  <div className="bg-primary text-primary-foreground rounded-lg p-3 max-w-[70%]">
                    <p className="text-sm">Hi John, this is a reminder about your appointment tomorrow at 10 AM.</p>
                    <p className="text-xs mt-1 opacity-70">10:00 AM</p>
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg p-3 max-w-[70%]">
                    <p className="text-sm">Thanks for the reminder! I'll be there.</p>
                    <p className="text-xs mt-1 opacity-70">10:30 AM</p>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Textarea placeholder="Type your message..." className="min-h-[80px]" />
                  <Button className="self-end">
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="reminders">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Patient</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Scheduled</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reminders.map((reminder) => (
                    <TableRow key={reminder.id}>
                      <TableCell className="font-medium">{reminder.patient}</TableCell>
                      <TableCell><Badge variant="outline">{reminder.type}</Badge></TableCell>
                      <TableCell>{reminder.scheduled}</TableCell>
                      <TableCell>
                        <Badge className={reminder.status === 'Sent' ? 'bg-green-500' : 'bg-yellow-500'}>
                          {reminder.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button size="sm" variant="outline">Edit</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates">
          <Card>
            <CardHeader>
              <CardTitle>Message Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium">Appointment Reminder</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Hi [patient_name], this is a reminder about your appointment on [date] at [time]. 
                    Reply YES to confirm or call us to reschedule.
                  </p>
                </div>
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium">Follow-up Reminder</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Hi [patient_name], it&apos;s time for your follow-up visit. 
                    Please call us to schedule your appointment.
                  </p>
                </div>
                <Button variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Template
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Communication Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">SMS Notifications</p>
                  <p className="text-sm text-muted-foreground">Enable SMS messaging</p>
                </div>
                <Button variant="outline">Configure</Button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">Enable email messaging</p>
                </div>
                <Button variant="outline">Configure</Button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Auto Reminders</p>
                  <p className="text-sm text-muted-foreground">Send automatic reminders</p>
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
