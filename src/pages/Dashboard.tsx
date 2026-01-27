import { useState, useEffect } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { StatCard } from '@/components/dashboard/StatCard';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { api } from '@/lib/api';
import { Search, FileText, CheckCircle, Wifi, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<{
    programsFound: number;
    pendingApprovals: number;
    applicationsSubmitted: number;
    connectedAgents: number;
  } | null>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, activityData] = await Promise.all([
          api.getDashboardStats(),
          api.getActivityFeed(),
        ]);
        setStats(statsData);
        setActivity(activityData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-8">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary to-primary/80 p-8 text-primary-foreground">
          <div className="relative z-10">
            <h2 className="text-2xl font-bold mb-2">Welcome back, Automated Online Profits! 👋</h2>
            <p className="text-primary-foreground/80 mb-4">
              Your AI agent is actively discovering and applying to affiliate programs for you.
            </p>
            <Button 
              variant="secondary" 
              className="gap-2"
              onClick={() => navigate('/programs')}
            >
              View Programs <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
          <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-primary-foreground/5 to-transparent" />
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {loading ? (
            <>
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-32 rounded-xl" />
              ))}
            </>
          ) : (
            <>
              <StatCard
                title="Programs Found"
                value={stats?.programsFound ?? 0}
                description="Total discovered programs"
                icon={Search}
                trend={{ value: 12, positive: true }}
              />
              <StatCard
                title="Pending Approvals"
                value={stats?.pendingApprovals ?? 0}
                description="Awaiting your review"
                icon={FileText}
              />
              <StatCard
                title="Applications"
                value={stats?.applicationsSubmitted ?? 0}
                description="Total submitted"
                icon={CheckCircle}
                trend={{ value: 8, positive: true }}
              />
              <StatCard
                title="Connected Agents"
                value={stats?.connectedAgents ?? 0}
                description="Active automation"
                icon={Wifi}
              />
            </>
          )}
        </div>

        {/* Quick Actions */}
        <div>
          <h3 className="text-lg font-semibold text-foreground mb-4">Quick Actions</h3>
          <QuickActions
            onDiscover={() => navigate('/programs?action=discover')}
            onApply={() => navigate('/applications?action=bulk')}
            onPublish={() => navigate('/tasks?filter=publish')}
          />
        </div>

        {/* Activity Feed */}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            {loading ? (
              <Skeleton className="h-96 rounded-xl" />
            ) : (
              <ActivityFeed items={activity} />
            )}
          </div>
          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-card p-6">
              <h4 className="font-semibold text-card-foreground mb-3">Getting Started</h4>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-muted-foreground">Connect local agent</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-muted-foreground">Set up response pool</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full border-2 border-muted-foreground" />
                  <span className="text-card-foreground">Discover first programs</span>
                </li>
                <li className="flex items-center gap-2">
                  <div className="h-4 w-4 rounded-full border-2 border-muted-foreground" />
                  <span className="text-card-foreground">Submit applications</span>
                </li>
              </ul>
              <Button variant="outline" size="sm" className="w-full mt-4">
                View Onboarding Guide
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
