import { Search, Send, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: typeof Search;
  onClick: () => void;
  variant?: 'default' | 'primary';
}

interface QuickActionsProps {
  onDiscover: () => void;
  onApply: () => void;
  onPublish: () => void;
  className?: string;
}

export function QuickActions({ onDiscover, onApply, onPublish, className }: QuickActionsProps) {
  const actions: QuickAction[] = [
    {
      id: 'discover',
      title: 'Discover Programs',
      description: 'Find new affiliate programs by keyword',
      icon: Search,
      onClick: onDiscover,
      variant: 'primary',
    },
    {
      id: 'apply',
      title: 'Bulk Apply',
      description: 'Apply to multiple programs at once',
      icon: Send,
      onClick: onApply,
    },
    {
      id: 'publish',
      title: 'Publish Queue',
      description: 'Review and publish pending content',
      icon: Upload,
      onClick: onPublish,
    },
  ];

  return (
    <div className={cn("grid gap-4 md:grid-cols-3", className)}>
      {actions.map((action) => (
        <Card 
          key={action.id}
          className={cn(
            "group cursor-pointer transition-all hover:shadow-lg",
            action.variant === 'primary' && "border-primary/50 bg-primary/5"
          )}
          onClick={action.onClick}
        >
          <CardHeader className="pb-2">
            <div className={cn(
              "flex h-10 w-10 items-center justify-center rounded-lg transition-colors mb-2",
              action.variant === 'primary' 
                ? "bg-primary text-primary-foreground" 
                : "bg-muted group-hover:bg-primary group-hover:text-primary-foreground"
            )}>
              <action.icon className="h-5 w-5" />
            </div>
            <CardTitle className="text-base">{action.title}</CardTitle>
            <CardDescription className="text-xs">{action.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              variant={action.variant === 'primary' ? 'default' : 'outline'} 
              size="sm" 
              className="w-full"
            >
              Get Started
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
