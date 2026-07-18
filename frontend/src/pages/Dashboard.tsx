import { useQuery } from '@tanstack/react-query';
import { fetchDashboard } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Activity, PlayCircle, CheckCircle2, Globe } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { RelativeTime } from '@/components/RelativeTime';

const STAGES = [
  { key: 'preflight', label: 'Preflight', short: 'PF' },
  { key: 'acquisition', label: 'Acquisition', short: 'ACQ' },
  { key: 'classification', label: 'Classification', short: 'CLS' },
  { key: 'selection', label: 'Selection', short: 'SEL' },
  { key: 'application', label: 'Application', short: 'APP' },
  { key: 'reconciliation', label: 'Reconciliation', short: 'REC' },
  { key: 'strategy', label: 'Strategy', short: 'STR' },
  { key: 'report', label: 'Report', short: 'REP' },
];

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

  const { summary, lifecycle: rawLifecycle, latest_run, system_health, upcoming_executions, top_companies, provider_health } = dashboard || {};
  const totalJobs = summary?.total_jobs || 0;
  const totalApplied = summary?.total_applied || 0;
  const applicationRate = totalJobs > 0 ? ((totalApplied / totalJobs) * 100).toFixed(1) : '0';

  // Map raw lifecycle stage names to human-readable labels for the chart
  const LIFECYCLE_LABELS: Record<string, string> = {
    UNKNOWN: 'Acquired',
    SUBMITTED: 'Submitted',
    VIEWED: 'Viewed',
    SHORTLISTED: 'Shortlisted',
    INTERVIEW: 'Interview',
    REJECTED: 'Rejected',
    OFFER: 'Offer',
  };
  const lifecycle = (rawLifecycle || []).map((d: any) => ({
    ...d,
    lifecycle_stage: LIFECYCLE_LABELS[d.lifecycle_stage] ?? d.lifecycle_stage,
  }));

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

        {/* Pipeline Stage Tracker */}
        <Card className="shadow-none border-border/50 bg-card/50">
          <CardHeader className="py-3">
            <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <PlayCircle className="w-4 h-4 text-primary" />
              Latest Run Stage Stepper ({latest_run?.run_id || 'No Run Active'})
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-2">
              {STAGES.map((stage, idx) => {
                const status = (latest_run?.stages?.[stage.key] || latest_run?.stage_results?.[stage.key] || 'PENDING').toUpperCase();
                let color = 'bg-muted text-muted-foreground border-muted-foreground/20';
                let statusLabel = 'Pending';
                if (status === 'SUCCESS') {
                  color = 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30 font-bold';
                  statusLabel = 'Success';
                } else if (status === 'FAILED') {
                  color = 'bg-rose-500/10 text-rose-500 border-rose-500/30 font-bold';
                  statusLabel = 'Failed';
                } else if (status === 'RUNNING' || status === 'IN_PROGRESS') {
                  color = 'bg-blue-500/10 text-blue-500 border-blue-500/30 font-bold animate-pulse';
                  statusLabel = 'Running';
                } else if (status === 'SKIPPED') {
                  color = 'bg-orange-500/10 text-orange-500 border-orange-500/20';
                  statusLabel = 'Skipped';
                }

                return (
                  <div key={stage.key} className="flex-1 w-full flex items-center gap-2">
                    <div className="flex flex-col items-center md:items-start flex-1">
                      <div className={`w-full border rounded-md p-2 flex items-center justify-between ${color}`}>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-1.5 py-0.5 bg-background/50 rounded font-mono">{stage.short}</span>
                          <span className="text-xs font-semibold">{stage.label}</span>
                        </div>
                        <span className="text-[10px] uppercase font-mono">{statusLabel}</span>
                      </div>
                    </div>
                    {idx < STAGES.length - 1 && (
                      <span className="hidden md:inline text-muted-foreground/30 text-lg">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

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

          {/* Provider Status & Health */}
          <Card className="col-span-1 shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Globe className="w-4 h-4 text-primary" />
                Provider Status & Health
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {['indeed', 'linkedin', 'google'].map((provider) => {
                const health = provider_health?.[provider] || { status: 'active', total_searches: 0, successful_searches: 0, success_rate: 1.0, average_latency_seconds: 0 };
                const name = provider === 'google' ? 'Google Jobs' : provider === 'indeed' ? 'Indeed' : 'LinkedIn';
                const status = (health.status || 'unknown').toLowerCase();
                
                let badgeColor = 'text-muted-foreground border-border bg-muted/20';
                if (status === 'active') {
                  badgeColor = 'text-green-500 border-green-500/20 bg-green-500/10';
                } else if (status === 'degraded') {
                  badgeColor = 'text-orange-500 border-orange-500/20 bg-orange-500/10';
                } else if (status === 'disabled' || status === 'offline') {
                  badgeColor = 'text-red-500 border-red-500/20 bg-red-500/10';
                }

                return (
                  <div key={provider} className="flex flex-col gap-2 border-b border-border/20 last:border-0 pb-3 last:pb-0">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-foreground capitalize">{name}</span>
                      <Badge variant="outline" className={`font-mono text-[9px] uppercase rounded-sm px-1.5 ${badgeColor}`}>
                        {status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[10px] text-muted-foreground font-mono">
                      <div>
                        <span className="block text-[8px] uppercase tracking-wider text-muted-foreground/60">Searches</span>
                        <span className="text-foreground font-medium">{health.total_searches || 0}</span>
                      </div>
                      <div>
                        <span className="block text-[8px] uppercase tracking-wider text-muted-foreground/60">Success %</span>
                        <span className="text-foreground font-medium">{Math.round((health.success_rate || 0) * 100)}%</span>
                      </div>
                      <div>
                        <span className="block text-[8px] uppercase tracking-wider text-muted-foreground/60">Latency</span>
                        <span className="text-foreground font-medium">{(health.average_latency_seconds || 0).toFixed(2)}s</span>
                      </div>
                    </div>
                  </div>
                );
              })}
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
