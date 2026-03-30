// ============================================
// CoreDent PMS - Header Component
// Top navigation with user menu
// ============================================

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Menu, Bell, LogOut, User as UserIcon, Settings } from 'lucide-react';
import { Breadcrumbs } from './Breadcrumbs';
import type { User, UserRole } from '@/types/api';
import { notificationsApi } from '@/services/api';

interface HeaderProps {
  user: User | null;
  onMenuToggle: () => void;
}

const roleLabels: Record<UserRole, string> = {
  owner: 'Owner',
  admin: 'Admin',
  dentist: 'Dentist',
  front_desk: 'Front Desk',
};

const roleColors: Record<UserRole, string> = {
  owner: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  admin: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  dentist: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  front_desk: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

export function Header({ user, onMenuToggle }: HeaderProps) {
  const { logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState<number | null>(null);

  useEffect(() => {
    let isActive = true;
    if (!user) {
      setUnreadCount(null);
      return () => {
        isActive = false;
      };
    }

    const loadUnread = async () => {
      const response = await notificationsApi.getUnreadCount();
      if (!isActive) return;
      if (response.success && response.data) {
        setUnreadCount(response.data.unreadCount);
      } else {
        setUnreadCount(0);
      }
    };

    loadUnread();

    return () => {
      isActive = false;
    };
  }, [user]);

  const getInitials = (firstName: string | undefined, lastName: string | undefined) => {
    if (!firstName || !lastName) return '?';
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-card px-4 lg:px-6">
      {/* Left side */}
      <div className="flex items-center gap-4 flex-1">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onMenuToggle}
        >
          <Menu className="h-5 w-5" />
        </Button>
        
        {user && (
          <div className="hidden lg:flex items-center gap-4 flex-1">
            <h2 className="text-lg font-semibold whitespace-nowrap">{user.practiceName}</h2>
            <Separator orientation="vertical" className="h-6 mx-2" />
            <Breadcrumbs />
          </div>
        )}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative" disabled={!user}>
          <Bell className="h-5 w-5" />
          {user && unreadCount && unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] text-destructive-foreground">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>

        {/* User Menu */}
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 px-2">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.avatarUrl} alt={user.firstName} />
                  <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                    {getInitials(user.firstName, user.lastName)}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:flex flex-col items-start">
                  <span className="text-sm font-medium leading-none">
                    {user.firstName} {user.lastName}
                  </span>
                  <Badge 
                    variant="secondary" 
                    className={`text-[10px] h-4 mt-1 px-1 ${roleColors[user.role]}`}
                  >
                    {roleLabels[user.role]}
                  </Badge>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col">
                  <span>{user.firstName} {user.lastName}</span>
                  <span className="text-xs text-muted-foreground font-normal">
                    {user.email}
                  </span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <UserIcon className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}
