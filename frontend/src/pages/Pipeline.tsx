import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchPipelineState, launchPipeline } from '@/lib/api';
import { Play, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { RelativeTime } from '@/components/RelativeTime';

export default function Pipeline() {
  const queryClient = useQueryClient();
  const [live, setLive] = useState(false);
  const [maxApplications, setMaxApplications] = useState(500);
  const [canary, setCanary] = useState(false);
  const [forceLive, setForceLive] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['pipeline_state'],
    queryFn: fetchPipelineState,
    refetchInterval: (query) => (query.state.data?.running ? 2000 : 5000),
  });

  const launchMutation = useMutation({
    mutationFn: launchPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline_state'] });
    }
  });

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [data?.log]);

  const handleLaunch = () => {
    if (live && !window.confirm("Live confirmation is required. Are you sure?")) return;
    launchMutation.mutate({ live, max_applications: maxApplications, canary, force_live: forceLive });
  };

  const isRunning = data?.running || false;
  const state = data?.state || {};

  if (isLoading && !data) {
    return <div className="p-4 text-sm text-muted-foreground">Loading pipeline state...</div>;
  }

  if (error) {
    return <div className="p-4 text-sm text-red-500">Error: {(error as Error).message}</div>;
  }

  return (
    <div className="h-full flex flex-col p-4 md:p-6 gap-6 max-w-[1600px] mx-auto overflow-y-auto pb-20">
      
      {/* Header */}
      <div className="flex flex-col gap-1 border-b pb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Operate</span>
          <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-mono font-bold", isRunning ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground")}>
            {isRunning ? "RUNNING" : "IDLE"}
          </span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight">Pipeline Control</h1>
        <p className="text-sm text-muted-foreground">Configure, execute, and observe the application engine.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Column: Logs */}
        <div className="flex-[1.8] flex flex-col gap-6 min-w-0">
          <div className="border border-border/50 bg-card rounded-md flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-border/50 bg-muted/20 flex flex-col">
              <h3 className="font-semibold text-sm">Live Output</h3>
              <p className="text-xs text-muted-foreground">Active launcher log</p>
            </div>
            <div className="p-4 bg-[#0b1017] h-[500px] overflow-y-auto font-mono text-[13px] text-[#9dacbf] leading-relaxed relative">
              <pre className="whitespace-pre-wrap">{data?.log}</pre>
              <div ref={logEndRef} />
            </div>
          </div>
        </div>

        {/* Right Column: Config & Telemetry */}
        <div className="flex-1 flex flex-col gap-6 min-w-[320px]">
          
          {/* Telemetry */}
          <div className="border border-border/50 bg-card rounded-md flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-border/50 bg-muted/20 flex flex-col">
              <h3 className="font-semibold text-sm">Live Process Telemetry</h3>
            </div>
            <div className="grid grid-cols-2 gap-px bg-border/50">
              <div className="bg-card p-4 flex flex-col gap-1">
                <span className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">Process</span>
                <span className="font-medium text-sm">{isRunning ? "RUNNING" : "IDLE"}</span>
              </div>
              <div className="bg-card p-4 flex flex-col gap-1">
                <span className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">PID</span>
                <span className="font-medium text-sm font-mono">{state.pid || '—'}</span>
              </div>
              <div className="bg-card p-4 flex flex-col gap-1">
                <span className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">Mode</span>
                <span className="font-medium text-sm">{state.live ? 'LIVE' : 'DRY RUN'}</span>
              </div>
              <div className="bg-card p-4 flex flex-col gap-1">
                <span className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider">Started</span>
                <span className="font-medium text-sm">{state.started_at ? <RelativeTime date={state.started_at} /> : '—'}</span>
              </div>
            </div>
          </div>

          {/* Config */}
          <div className="border border-border/50 bg-card rounded-md flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-border/50 bg-muted/20 flex flex-col">
              <h3 className="font-semibold text-sm">Run Configuration</h3>
              <p className="text-xs text-muted-foreground">Safety-first execution controls</p>
            </div>
            <div className="p-4 flex flex-col gap-4">
              <div className="flex gap-2 p-1 bg-muted rounded-md w-full">
                <button 
                  className={cn("flex-1 text-sm py-1.5 rounded-sm transition-colors", !live ? "bg-background shadow-sm font-medium" : "text-muted-foreground hover:text-foreground")}
                  onClick={() => { setLive(false); setMaxApplications(500); }}
                  disabled={isRunning}
                >
                  Dry Run
                </button>
                <button 
                  className={cn("flex-1 text-sm py-1.5 rounded-sm transition-colors", live ? "bg-background shadow-sm font-medium text-red-500" : "text-muted-foreground hover:text-foreground")}
                  onClick={() => { setLive(true); setMaxApplications(3); }}
                  disabled={isRunning}
                >
                  Live
                </button>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium">Application Ceiling</label>
                <input 
                  type="number" 
                  value={maxApplications}
                  onChange={(e) => setMaxApplications(Number(e.target.value))}
                  disabled={isRunning}
                  className="bg-background border border-border rounded-md px-3 py-1.5 text-sm"
                  min="1"
                  max="1000"
                />
              </div>

              {live && (
                <div className="flex flex-col gap-3 pt-2 border-t border-border/50">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={canary} onChange={(e) => setCanary(e.target.checked)} disabled={isRunning} />
                    Canary · one live application
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={forceLive} onChange={(e) => setForceLive(e.target.checked)} disabled={isRunning} />
                    Force Live · Bypass cooldown
                  </label>
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md flex gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                    <p className="text-xs text-red-500 font-medium">I understand LIVE mode can submit applications and consume quota.</p>
                  </div>
                </div>
              )}

              <button 
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-sm py-2 rounded-md shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors mt-2"
                onClick={handleLaunch}
                disabled={isRunning || launchMutation.isPending}
              >
                {launchMutation.isPending ? "Starting..." : isRunning ? "Running" : "Launch Pipeline"}
                {!isRunning && <Play className="w-4 h-4" />}
              </button>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
