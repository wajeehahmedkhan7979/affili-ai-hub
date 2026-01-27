import { formatDistanceToNow } from 'date-fns';
import { Search, FileText, CheckCircle, Wifi, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ActivityItem {
  id: string;
  type: 'discovery' | 'application' | 'approval' | 'agent' | 'warning';
  message: string;
  timestamp: string;
}

interface ActivityFeedProps {
  items: ActivityItem[];
  className?: string;
}

const typeIcons = {
  discovery: Search,
  application: FileText,
  approval: CheckCircle,
  agent: Wifi,
  warning: AlertTriangle,
};

const typeColors = {
  discovery: 'bg-blue-500/10 text-blue-600',
  application: 'bg-primary/10 text-primary',
  approval: 'bg-green-500/10 text-green-600',
  agent: 'bg-emerald-500/10 text-emerald-600',
  warning: 'bg-amber-500/10 text-amber-600',
};

export function ActivityFeed({ items, className }: ActivityFeedProps) {
  return (
    <div className={cn("rounded-xl border border-border bg-card", className)}>
      <div className="border-b border-border px-6 py-4">
        <h3 className="font-semibold text-card-foreground">Recent Activity</h3>
      </div>
      <div className="divide-y divide-border">
        {items.map((item) => {
          const Icon = typeIcons[item.type];
          return (
            <div key={item.id} className="flex items-start gap-4 px-6 py-4">
              <div className={cn(
                "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full",
                typeColors[item.type]
              )}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-card-foreground">{item.message}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
