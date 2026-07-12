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

  const { summary, lifecycle, latest_run } = dashboard || {};
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

          {/* Backend Enhancement Notice */}
          <Card className="col-span-1 shadow-none border-dashed border-border/50 bg-muted/10 flex flex-col">
            <CardHeader>
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                Missing Metrics
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-center space-y-4">
              <p className="text-xs text-muted-foreground leading-relaxed">
                <strong className="text-foreground">Backend Enhancement Opportunity:</strong> The PRD requires visibility into System Health, Pipeline Health, Scheduler State, Top Companies, and Upcoming Executions on the dashboard.
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Currently, the <code>/api/dashboard</code> endpoint only provides aggregated summary counts, lifecycle distribution, and the latest run metadata. 
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                To maintain trust and avoid fabricating operational metrics, these have been intentionally omitted until backend telemetry APIs are exposed.
              </p>
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
