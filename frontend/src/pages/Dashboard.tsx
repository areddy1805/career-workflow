import { useQuery } from '@tanstack/react-query';
import { fetchDashboard } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Activity, AlertTriangle, PlayCircle, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { RelativeTime } from '@/components/RelativeTime';

export default function Dashboard() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
  });

  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-background p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-muted w-1/4 rounded" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-muted rounded-md" />)}
          </div>
        </div>
      </div>
    );
  }

  const { summary, lifecycle, latest_run, system_health, upcoming_executions, top_companies } = dashboard || {};
  const totalJobs = summary?.total_jobs || 0;
  const totalApplied = summary?.total_applied || 0;
  const applicationRate = totalJobs > 0 ? ((totalApplied / totalJobs) * 100).toFixed(1) : '0';

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold text-lg tracking-tight">Executive Dashboard</h2>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-8">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <DatabaseIcon className="w-3.5 h-3.5" /> Total Ingested Jobs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight">{totalJobs.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5" /> Total Applied
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight text-primary">{totalApplied.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Activity className="w-3.5 h-3.5" /> Conversion Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight">{applicationRate}%</div>
            </CardContent>
          </Card>
          
          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <PlayCircle className="w-3.5 h-3.5" /> Latest Run Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <div className="text-lg font-semibold tracking-tight truncate max-w-[120px]" title={latest_run?.run_id}>
                  {latest_run?.run_id ? latest_run.run_id.split('T')[0] : 'None'}
                </div>
                {latest_run?.status && (
                  <Badge variant="outline" className={`font-mono text-[10px] uppercase rounded-sm border px-1.5 ${latest_run.status === 'SUCCESS' ? 'text-green-500 border-green-500/20 bg-green-500/10' : 'text-red-500 border-red-500/20 bg-red-500/10'}`}>
                    {latest_run.status}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {latest_run?.started_at ? <RelativeTime date={latest_run.started_at} /> : 'Unknown time'}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Funnel Chart */}
          <Card className="col-span-2 shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Pipeline Funnel</CardTitle>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={lifecycle} layout="vertical" margin={{ left: 50, right: 20, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                  <XAxis type="number" tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                  <YAxis dataKey="lifecycle_stage" type="category" width={100} tick={{ fontSize: 10, fill: 'hsl(var(--foreground))' }} />
                  <Tooltip 
                    cursor={{ fill: 'hsl(var(--muted)/0.5)' }}
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '4px', fontSize: '12px' }} 
                  />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 2, 2, 0]} maxBarSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* System Health */}
          <Card className="col-span-1 shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                System Health
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Status</span>
                <Badge variant="outline" className={system_health?.status === 'HEALTHY' ? 'text-green-500 border-green-500' : system_health?.status === 'WARNING' ? 'text-orange-500 border-orange-500' : ''}>
                  {system_health?.status || 'UNKNOWN'}
                </Badge>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Scheduler</span>
                <span>{system_health?.scheduler_running ? 'Running' : 'Stopped'}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted-foreground">Pipeline</span>
                <span>{system_health?.pipeline_running ? 'Active' : 'Idle'}</span>
              </div>
              <div className="flex justify-between items-center text-xs border-t pt-3">
                <span className="text-muted-foreground">Disk Usage</span>
                <span>{system_health?.disk_usage_pct}%</span>
              </div>
            </CardContent>
          </Card>

          {/* Top Companies */}
          <Card className="col-span-1 shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <DatabaseIcon className="w-4 h-4 text-primary" />
                Top Companies
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {top_companies?.map((c: any, i: number) => (
                <div key={i} className="flex justify-between items-center text-xs border-b border-border/20 last:border-0 pb-2 last:pb-0">
                  <span className="truncate max-w-[150px] font-medium" title={c.name}>{c.name}</span>
                  <span className="text-muted-foreground">{c.count} applications</span>
                </div>
              ))}
              {!top_companies?.length && <p className="text-xs text-muted-foreground text-center">No data available.</p>}
            </CardContent>
          </Card>
          
          {/* Upcoming Executions */}
          <Card className="col-span-1 shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <PlayCircle className="w-4 h-4 text-primary" />
                Upcoming Executions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcoming_executions?.map((e: any, i: number) => (
                <div key={i} className="flex justify-between items-center text-xs border-b border-border/20 last:border-0 pb-2 last:pb-0">
                  <span className="font-medium">{e.task}</span>
                  <span className="text-muted-foreground"><RelativeTime date={e.scheduled_for} /></span>
                </div>
              ))}
              {!upcoming_executions?.length && <p className="text-xs text-muted-foreground text-center">No scheduled executions.</p>}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function DatabaseIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  )
}
