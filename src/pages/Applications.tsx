import { useState, useEffect } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { api } from '@/lib/api';
import { Application } from '@/lib/mock-data';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Clock, XCircle, Loader2, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';

const statusConfig: Record<string, { icon: typeof Clock; color: string; bgColor: string }> = {
  PendingApproval: { icon: Clock, color: 'text-amber-600', bgColor: 'bg-amber-500/10' },
  Submitted: { icon: Loader2, color: 'text-blue-600', bgColor: 'bg-blue-500/10' },
  Approved: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-500/10' },
  Rejected: { icon: XCircle, color: 'text-destructive', bgColor: 'bg-destructive/10' },
};

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadApplications();
  }, []);

  async function loadApplications() {
    setLoading(true);
    try {
      const data = await api.getApplications();
      setApplications(data);
    } catch (error) {
      console.error('Failed to load applications:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout title="Applications">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <p className="text-muted-foreground">
            Track and manage your affiliate program applications
          </p>
        </div>

        {/* Applications Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-xl" />
            ))
          ) : applications.length === 0 ? (
            <Card className="md:col-span-2 lg:col-span-3">
              <CardContent className="py-12 text-center text-muted-foreground">
                No applications yet. Start by applying to programs from the Programs page.
              </CardContent>
            </Card>
          ) : (
            applications.map((app) => {
              const config = statusConfig[app.status];
              const Icon = config.icon;

              return (
                <Card key={app.id} className="overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary font-semibold">
                          {app.program?.name?.charAt(0) || 'P'}
                        </div>
                        <div>
                          <CardTitle className="text-base">{app.program?.name || 'Unknown Program'}</CardTitle>
                          <CardDescription className="text-xs">
                            {app.program?.network}
                          </CardDescription>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Status */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={cn("flex h-8 w-8 items-center justify-center rounded-full", config.bgColor)}>
                          <Icon className={cn("h-4 w-4", config.color, app.status === 'Submitted' && "animate-spin")} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-card-foreground">{app.status}</p>
                          <p className="text-xs text-muted-foreground">{app.agent_status}</p>
                        </div>
                      </div>
                      <Badge variant="outline">{app.program?.commission || 'N/A'}</Badge>
                    </div>

                    {/* Timeline */}
                    <div className="text-xs text-muted-foreground">
                      Applied {formatDistanceToNow(new Date(app.created_at), { addSuffix: true })}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      {app.status === 'PendingApproval' && (
                        <>
                          <Button size="sm" className="flex-1">Approve</Button>
                          <Button size="sm" variant="outline" className="flex-1">Edit</Button>
                        </>
                      )}
                      {app.status === 'Approved' && (
                        <Button size="sm" variant="outline" className="w-full gap-2">
                          <ExternalLink className="h-3 w-3" />
                          View Program
                        </Button>
                      )}
                    </div>
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
