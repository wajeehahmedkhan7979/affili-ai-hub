import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { api } from '@/lib/api';
import { Task } from '@/lib/mock-data';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Play, 
  Pause, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Upload,
  Eye
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';

const statusConfig: Record<string, { icon: typeof Clock; color: string; label: string }> = {
  PENDING: { icon: Clock, color: 'bg-muted text-muted-foreground', label: 'Pending' },
  RUNNING: { icon: Play, color: 'bg-blue-500/10 text-blue-600', label: 'Running' },
  COMPLETED: { icon: CheckCircle, color: 'bg-green-500/10 text-green-600', label: 'Completed' },
  FAILED: { icon: AlertTriangle, color: 'bg-destructive/10 text-destructive', label: 'Failed' },
  PAUSED_FOR_CAPTCHA: { icon: Pause, color: 'bg-amber-500/10 text-amber-600', label: 'Captcha Required' },
};

const typeLabels: Record<string, string> = {
  APPLY_PROGRAM: 'Apply to Program',
  DISCOVER_PROGRAMS: 'Discover Programs',
  PUBLISH_CONTENT: 'Publish Content',
};

export default function Tasks() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTask, setExpandedTask] = useState<string | null>(null);

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    setLoading(true);
    try {
      const data = await api.getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleResumeTask(taskId: string) {
    try {
      await api.updateTask(taskId, { status: 'RUNNING' });
      toast({
        title: "Task Resumed",
        description: "The task has been resumed successfully.",
      });
      loadTasks();
    } catch (error) {
      toast({
        title: "Failed to Resume",
        description: "There was an error resuming the task.",
        variant: "destructive",
      });
    }
  }

  return (
    <AppLayout title="Tasks">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-muted-foreground">
              Monitor and manage automation tasks
            </p>
          </div>
          <Button variant="outline" onClick={loadTasks} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Task List */}
        <div className="space-y-4">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))
          ) : tasks.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                No tasks found. Tasks will appear here when you start automations.
              </CardContent>
            </Card>
          ) : (
            tasks.map((task) => {
              const config = statusConfig[task.status];
              const Icon = config.icon;
              const isExpanded = expandedTask === task.id;

              return (
                <Card key={task.id} className="overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", config.color)}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base">{typeLabels[task.type]}</CardTitle>
                          <CardDescription className="text-xs">
                            {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={cn("border-0", config.color)}>
                          {config.label}
                        </Badge>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => navigate(`/tasks/${task.id}`)}
                          className="gap-1"
                        >
                          <Eye className="h-3 w-3" />
                          View
                        </Button>
                        {task.status === 'PAUSED_FOR_CAPTCHA' && (
                          <Button size="sm" onClick={() => handleResumeTask(task.id)} className="gap-1">
                            <Upload className="h-3 w-3" />
                            Resume
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {/* Task Details */}
                    <div className="text-sm text-muted-foreground mb-2">
                      {Object.entries(task.payload).map(([key, value]) => (
                        <span key={key} className="mr-4">
                          <span className="font-medium">{key}:</span> {value}
                        </span>
                      ))}
                    </div>

                    {/* Logs Toggle */}
                    {task.logs.length > 0 && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="px-0 text-xs"
                          onClick={() => setExpandedTask(isExpanded ? null : task.id)}
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-3 w-3 mr-1" />
                              Hide Logs
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3 w-3 mr-1" />
                              Show Logs ({task.logs.length})
                            </>
                          )}
                        </Button>
                        {isExpanded && (
                          <div className="mt-3 rounded-lg bg-muted/50 p-3 font-mono text-xs space-y-1">
                            {task.logs.map((log, i) => (
                              <p key={i} className="text-muted-foreground">{log}</p>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </AppLayout>
  );
}
