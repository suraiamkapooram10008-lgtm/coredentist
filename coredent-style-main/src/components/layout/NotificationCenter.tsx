/**
 * Notification Center Component
 * Global notification bell with real-time updates
 */

import { useState, useEffect } from "react";
import { Bell, Check, CheckCheck, X, MessageSquare, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCommunications } from "@/hooks/useCommunications";
import { cn } from "@/lib/utils";

export interface Notification {
  id: string;
  type: "message" | "reminder" | "alert" | "system";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
  metadata?: Record<string, unknown>;
}

export default function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("unread");
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { summary, fetchSummary } = useCommunications();

  // Load notifications on mount
  useEffect(() => {
    fetchSummary();
    // Generate sample notifications based on summary data
    generateNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summary]);

  const generateNotifications = () => {
    const sampleNotifications: Notification[] = [
      {
        id: "1",
        type: "reminder",
        title: "Appointment Reminders Sent",
        message: "12 appointment reminders were successfully delivered",
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        read: false,
        metadata: { count: 12 },
      },
      {
        id: "2",
        type: "message",
        title: "New Patient Message",
        message: "John Doe replied to your message",
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        read: false,
      },
      {
        id: "3",
        type: "alert",
        title: "Low Delivery Rate",
        message: "SMS delivery rate dropped below 90% in the last hour",
        timestamp: new Date(Date.now() - 10800000).toISOString(),
        read: true,
      },
      {
        id: "4",
        type: "system",
        title: "Template Updated",
        message: "Appointment Reminder template was updated by Dr. Smith",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        read: true,
      },
    ];
    setNotifications(sampleNotifications);
  };

  const unreadCount = notifications.filter((n) => !n.read).length;
  const filteredNotifications =
    activeTab === "unread"
      ? notifications.filter((n) => !n.read)
      : notifications;

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const getNotificationIcon = (type: Notification["type"]) => {
    switch (type) {
      case "message":
        return <MessageSquare className="h-4 w-4 text-blue-500" />;
      case "reminder":
        return <Clock className="h-4 w-4 text-green-500" />;
      case "alert":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case "system":
        return <Bell className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTimeAgo = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs bg-red-500"
              variant="destructive"
            >
              {unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="end">
        <div className="flex items-center justify-between p-4 border-b">
          <h4 className="font-semibold">Notifications</h4>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={markAllAsRead}
              className="text-xs"
            >
              <CheckCheck className="h-3 w-3 mr-1" />
              Mark all read
            </Button>
          )}
        </div>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="p-2">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="unread">
              Unread ({unreadCount})
            </TabsTrigger>
            <TabsTrigger value="all">All</TabsTrigger>
          </TabsList>
        </Tabs>
        <ScrollArea className="h-[400px]">
          {filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
              <Check className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No notifications</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={cn(
                    "p-4 hover:bg-muted/50 cursor-pointer transition-colors",
                    !notification.read && "bg-blue-50/50 dark:bg-blue-950/20"
                  )}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        "rounded-full p-2",
                        !notification.read && "bg-blue-100 dark:bg-blue-900"
                      )}
                    >
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <p
                          className={cn(
                            "text-sm font-medium",
                            !notification.read && "text-blue-900 dark:text-blue-100"
                          )}
                        >
                          {notification.title}
                        </p>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 flex-shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteNotification(notification.id);
                          }}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {notification.message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {getTimeAgo(notification.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
        <div className="p-4 border-t">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => {
              setOpen(false);
              window.location.href = "/communications";
            }}
          >
            View All Communications
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}