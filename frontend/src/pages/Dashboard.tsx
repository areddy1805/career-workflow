import { useQuery } from '@tanstack/react-query';
import { fetchDashboard, fetchRuntime } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, Play, Settings, ShieldCheck, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 10000,
  });

  const { data: runtime, isLoading: runLoading } = useQuery({
    queryKey: ['runtime'],
    queryFn: fetchRuntime,
    refetchInterval: 5000,
  });

  if (dashLoading || runLoading) {
    return (
      <div className="p-8 space-y-6">
        <h2 className="text-3xl font-bold tracking-tight mb-6">Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1,2,3,4,5,6,7,8].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}
        </div>
      </div>
    );
  }

  const { summary, lifecycle, latest_run } = dashboard || {};
  const { scheduler, pipeline } = runtime || {};

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">Welcome to your Career Workflow Console.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Play className="w-4 h-4 mr-2" /> Start Scheduler
          </Button>
          <Button variant="outline" size="sm">
            <Activity className="w-4 h-4 mr-2" /> Run Pipeline
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduler Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <Badge variant={scheduler?.status === 'RUNNING' ? 'default' : 'secondary'}>
                {scheduler?.status || 'UNKNOWN'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {scheduler?.is_alive ? 'Process active' : 'Process stopped'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pipeline Status</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <Badge variant={pipeline?.status === 'RUNNING' ? 'default' : 'outline'}>
                {pipeline?.status || 'IDLE'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Heartbeat</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {scheduler?.heartbeat_age ? `${Math.round(scheduler.heartbeat_age)}s ago` : 'N/A'}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Lifecycle Funnel</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lifecycle} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="lifecycle_stage" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Latest Run Overview</CardTitle>
          </CardHeader>
          <CardContent>
            {latest_run ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Run ID</span>
                  <span>{latest_run._run_dir?.split('/').pop() || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Status</span>
                  <Badge variant={latest_run.status === 'SUCCESS' ? 'default' : 'destructive'}>
                    {latest_run.status || 'UNKNOWN'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Acquired</span>
                  <span>{latest_run.counts?.acquired || latest_run.acquired || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Submitted</span>
                  <span>{latest_run.submitted || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Failed</span>
                  <span className="text-destructive font-medium">{latest_run.failed || 0}</span>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">No recent run found.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
