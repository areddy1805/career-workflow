import { useQuery } from '@tanstack/react-query';
import { fetchDashboard } from '@/lib/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { BarChart2, AlertTriangle } from 'lucide-react';

export default function Analytics() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
  });

  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-background p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-muted w-1/4 rounded" />
          <div className="h-96 bg-muted rounded-md" />
        </div>
      </div>
    );
  }

  const { lifecycle } = dashboard || {};

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold text-lg tracking-tight flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-primary" />
          Analytics Engine
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pipeline Funnel */}
          <div className="border border-border/50 rounded-md bg-card/30 flex flex-col">
            <div className="h-10 px-4 border-b bg-secondary/30 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Pipeline Funnel
            </div>
            <div className="p-4 h-[350px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={lifecycle} layout="vertical" margin={{ left: 50, right: 20, top: 10, bottom: 0 }}>
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
            </div>
          </div>

          {/* Enhancement Opportunity */}
          <div className="border border-dashed border-border/50 rounded-md bg-muted/10 flex flex-col items-center justify-center p-8 text-center">
            <AlertTriangle className="w-8 h-8 text-orange-500 mb-4" />
            <h3 className="text-sm font-semibold mb-2">Backend Enhancement Required</h3>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-md">
              Additional analytic dimensions (Success/Failure trends, Daily throughput, Application velocity) are currently limited by the <code>/api/dashboard</code> endpoint scope. Once the backend telemetry is expanded, sophisticated Area and Stacked Bar charts will automatically populate here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
