import { useQuery } from '@tanstack/react-query';
import { fetchRuntime } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Activity, Server, Clock, Lock, Cpu } from 'lucide-react';

export default function Runtime() {
  const { data: runtime, isLoading } = useQuery({
    queryKey: ['runtime'],
    queryFn: fetchRuntime,
    refetchInterval: 3000,
  });

  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-background">
        <div className="p-6 animate-pulse space-y-4">
          <div className="h-4 bg-muted w-1/4 rounded" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </div>
    );
  }

  const { scheduler, pipeline, ui, latest_run_details } = runtime || {};

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold text-lg tracking-tight flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          Runtime Monitor
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-6 max-w-4xl space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Scheduler Module */}
          <div className="border border-border/50 rounded-md bg-card/30 flex flex-col">
            <div className="h-10 px-4 border-b bg-secondary/30 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Clock className="w-4 h-4" /> Scheduler
            </div>
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">Status</span>
                <Badge variant="outline" className={`font-mono text-[10px] rounded-sm px-1.5 ${scheduler?.status === 'RUNNING' ? 'text-green-500 border-green-500/20 bg-green-500/10' : scheduler?.status === 'STALE' ? 'text-red-500 border-red-500/20 bg-red-500/10' : 'text-muted-foreground'}`}>
                  {scheduler?.status || 'UNKNOWN'}
                </Badge>
              </div>
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">Process Alive</span>
                <span className="font-mono text-xs">{scheduler?.is_alive ? 'True' : 'False'}</span>
              </div>
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">Heartbeat Age</span>
                <span className="font-mono text-xs">{scheduler?.heartbeat_age ? `${Math.round(scheduler.heartbeat_age)}s` : 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-xs font-medium">PID</span>
                <span className="font-mono text-xs text-primary">{scheduler?.pid || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Pipeline Module */}
          <div className="border border-border/50 rounded-md bg-card/30 flex flex-col">
            <div className="h-10 px-4 border-b bg-secondary/30 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Cpu className="w-4 h-4" /> Pipeline Worker
            </div>
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">State</span>
                <Badge variant="outline" className={`font-mono text-[10px] rounded-sm px-1.5 ${pipeline?.status === 'RUNNING' ? 'text-green-500 border-green-500/20 bg-green-500/10' : 'text-muted-foreground'}`}>
                  {pipeline?.status || 'IDLE'}
                </Badge>
              </div>
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">Process Alive</span>
                <span className="font-mono text-xs">{pipeline?.is_alive ? 'True' : 'False'}</span>
              </div>
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">Execution Lock</span>
                <div className="flex items-center gap-1.5 font-mono text-xs">
                  {scheduler?.lock ? <Lock className="w-3 h-3 text-red-500" /> : <Lock className="w-3 h-3 text-muted-foreground/30" />}
                  {scheduler?.lock ? <span className="text-red-500">LOCKED</span> : <span>FREE</span>}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-xs font-medium">PID</span>
                <span className="font-mono text-xs text-primary">{pipeline?.pid || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* UI Server Module */}
          <div className="border border-border/50 rounded-md bg-card/30 flex flex-col md:col-span-2 lg:col-span-1">
            <div className="h-10 px-4 border-b bg-secondary/30 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Server className="w-4 h-4" /> Core API (UI Server)
            </div>
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-border/40 pb-2">
                <span className="text-muted-foreground text-xs font-medium">Status</span>
                <Badge variant="outline" className="font-mono text-[10px] rounded-sm px-1.5 text-green-500 border-green-500/20 bg-green-500/10">
                  {ui?.status || 'ONLINE'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-xs font-medium">PID</span>
                <span className="font-mono text-xs text-primary">{ui?.pid || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Latest Run Telemetry */}
        {latest_run_details && latest_run_details.run_id && (
          <div className="space-y-6 pt-4 border-t border-border/50">
            <h3 className="text-base font-semibold tracking-tight flex items-center gap-2 text-foreground">
              <Cpu className="w-5 h-5 text-primary" />
              Latest Run Telemetry
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Run Overview */}
              <div className="border border-border/50 rounded-md bg-card/30 p-4 space-y-3">
                <div className="flex justify-between items-center pb-2 border-b">
                  <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">Run Overview</span>
                  <Badge variant="outline" className={`font-mono text-[10px] uppercase rounded-sm px-1.5 
                    ${latest_run_details.status === 'SUCCESS' ? 'text-green-500 border-green-500/20 bg-green-500/10' : 
                      latest_run_details.status === 'RUNNING' ? 'text-blue-500 border-blue-500/20 bg-blue-500/10 animate-pulse' : 
                      'text-red-500 border-red-500/20 bg-red-500/10'}`}>
                    {latest_run_details.status || 'UNKNOWN'}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  <div className="text-muted-foreground">Run ID</div>
                  <div className="font-mono text-right truncate" title={latest_run_details.run_id}>{latest_run_details.run_id}</div>
                  
                  <div className="text-muted-foreground">Started At</div>
                  <div className="text-right">{latest_run_details.started_at ? new Date(latest_run_details.started_at).toLocaleString() : 'N/A'}</div>

                  <div className="text-muted-foreground">Completed At</div>
                  <div className="text-right">{latest_run_details.completed_at ? new Date(latest_run_details.completed_at).toLocaleString() : 'Running...'}</div>
                </div>
              </div>

              {/* Stage Stepper / Progress */}
              <div className="border border-border/50 rounded-md bg-card/30 p-4 space-y-3">
                <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider block pb-2 border-b">Stage Checklist</span>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                  {Object.entries(latest_run_details.stages || {}).map(([stage, status]: any) => {
                    const uppercaseStatus = String(status).toUpperCase();
                    let color = 'text-muted-foreground';
                    if (uppercaseStatus === 'SUCCESS') color = 'text-green-500 font-semibold';
                    else if (uppercaseStatus === 'FAILED') color = 'text-red-500 font-semibold';
                    else if (uppercaseStatus === 'RUNNING' || uppercaseStatus === 'IN_PROGRESS') color = 'text-blue-500 font-semibold animate-pulse';
                    return (
                      <div key={stage} className="flex justify-between items-center py-0.5 border-b border-border/20">
                        <span className="capitalize">{stage}</span>
                        <span className={`font-mono text-[10px] ${color}`}>{uppercaseStatus}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Acquisition Metrics */}
              <div className="border border-border/50 rounded-md bg-card/30 p-4 space-y-3">
                <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider block pb-2 border-b">Acquisition Metrics</span>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  <div className="text-muted-foreground">Jobs Acquired</div>
                  <div className="font-mono text-right">{latest_run_details.acquisition?.jobs ?? latest_run_details.acquisition?.acquired ?? 'N/A'}</div>
                  
                  <div className="text-muted-foreground">Search Requests</div>
                  <div className="font-mono text-right">{latest_run_details.acquisition?.search_requests_attempted ?? 'N/A'}</div>

                  <div className="text-muted-foreground">Challenge Blocked</div>
                  <div className="text-right">{latest_run_details.acquisition?.challenge_encountered ? 'Yes' : 'No'}</div>
                </div>
              </div>

              {/* Classification Metrics */}
              <div className="border border-border/50 rounded-md bg-card/30 p-4 space-y-3">
                <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider block pb-2 border-b">Classification Metrics</span>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  <div className="text-muted-foreground">Enriched & Classified</div>
                  <div className="font-mono text-right">{latest_run_details.classification?.summary?.classified ?? 'N/A'}</div>
                  
                  <div className="text-muted-foreground">Description Duplicates</div>
                  <div className="font-mono text-right">{latest_run_details.classification?.summary?.description_duplicates_removed ?? 'N/A'}</div>

                  <div className="text-muted-foreground">Prefilter Rejections</div>
                  <div className="font-mono text-right">{latest_run_details.classification?.rejected_count ?? 'N/A'}</div>
                </div>
              </div>

              {/* Selection Metrics */}
              <div className="border border-border/50 rounded-md bg-card/30 p-4 space-y-3">
                <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider block pb-2 border-b">Selection & Routing</span>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  <div className="text-muted-foreground">AI Scored / Ranked</div>
                  <div className="font-mono text-right">{latest_run_details.selection?.ranked ?? 'N/A'}</div>
                  
                  <div className="text-muted-foreground">Routing Eligible</div>
                  <div className="font-mono text-right">{latest_run_details.selection?.hard_gate_eligible ?? 'N/A'}</div>

                  <div className="text-muted-foreground">Routing Blocked</div>
                  <div className="font-mono text-right">{latest_run_details.selection?.hard_gate_rejected ?? 'N/A'}</div>
                </div>
              </div>

              {/* Application/Submission Metrics */}
              <div className="border border-border/50 rounded-md bg-card/30 p-4 space-y-3">
                <span className="font-semibold text-xs text-muted-foreground uppercase tracking-wider block pb-2 border-b">Application / Queue Actions</span>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  <div className="text-muted-foreground">Submitted (Live)</div>
                  <div className="font-mono text-right text-primary font-semibold">{latest_run_details.application?.submitted ?? 'N/A'}</div>
                  
                  <div className="text-muted-foreground">Dry Run Skipped</div>
                  <div className="font-mono text-right">{latest_run_details.application?.dry_run_skipped ?? 'N/A'}</div>

                  <div className="text-muted-foreground">Sent to Manual Review</div>
                  <div className="font-mono text-right text-orange-500 font-semibold">{latest_run_details.application?.manual_review ?? 'N/A'}</div>

                  <div className="text-muted-foreground">Application Failures</div>
                  <div className="font-mono text-right text-red-500 font-semibold">{latest_run_details.application?.failed ?? 'N/A'}</div>
                </div>
              </div>
            </div>

            {/* Error Telemetry */}
            {latest_run_details.errors && latest_run_details.errors.length > 0 && (
              <div className="border border-red-500/20 rounded-md bg-red-500/5 p-4 space-y-2">
                <span className="font-semibold text-xs text-red-500 uppercase tracking-wider block">Runtime Errors Detected</span>
                <ul className="space-y-1 text-xs text-red-500/80 font-mono">
                  {latest_run_details.errors.map((err: string, i: number) => (
                    <li key={i} className="flex gap-2 items-start">
                      <span className="shrink-0">•</span>
                      <span>{err}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
