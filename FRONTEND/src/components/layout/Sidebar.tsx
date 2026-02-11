import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  Search, 
  FileText, 
  ListTodo, 
  Database, 
  Settings, 
  Plug,
  Server,
  ChevronLeft,
  ChevronRight,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Programs', href: '/programs', icon: Search },
  { name: 'Applications', href: '/applications', icon: FileText },
  { name: 'Tasks', href: '/tasks', icon: ListTodo },
  { name: 'Response Pool', href: '/response-pool', icon: Database },
  { name: 'Agent Setup', href: '/agent', icon: Server },
  { name: 'Integrations', href: '/integrations', icon: Plug },
  { name: 'Settings', href: '/settings', icon: Settings },
];

interface SidebarProps {
  agentConnected?: boolean;
  isDemo?: boolean;
}

export function Sidebar({ agentConnected = true, isDemo = false }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside 
      className={cn(
        "fixed left-0 top-0 z-40 h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-sidebar-border">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Zap className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-bold text-lg text-sidebar-foreground">AFFILI-AI</span>
            </div>
          )}
          {collapsed && (
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary mx-auto">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-2 py-4 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href));
            
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  collapsed && "justify-center px-2"
                )}
                title={collapsed ? item.name : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && <span>{item.name}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Agent Status */}
        <div className={cn("px-3 py-4 border-t border-sidebar-border", collapsed && "px-2")}>
          <div className={cn(
            "flex items-center gap-2 rounded-lg px-3 py-2 bg-sidebar-accent",
            collapsed && "justify-center px-2"
          )}>
            <div className={cn(
              "h-2 w-2 rounded-full",
              agentConnected ? "bg-green-500 animate-pulse" : "bg-destructive"
            )} />
            {!collapsed && (
              <span className="text-xs text-sidebar-foreground">
                {isDemo ? 'Demo Mode' : agentConnected ? 'Agent Connected' : 'Agent Disconnected'}
              </span>
            )}
          </div>
        </div>

        {/* Collapse Toggle */}
        <div className="px-2 py-2 border-t border-sidebar-border">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-center"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </aside>
  );
}
