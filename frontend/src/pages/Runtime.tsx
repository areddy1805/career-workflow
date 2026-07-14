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

  const { scheduler, pipeline, ui } = runtime || {};

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
      </div>
    </div>
  );
}
