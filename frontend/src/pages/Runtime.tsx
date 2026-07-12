import { useQuery } from '@tanstack/react-query';
import { fetchRuntime } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, Server, Clock } from 'lucide-react';

export default function Runtime() {
  const { data: runtime, isLoading } = useQuery({
    queryKey: ['runtime'],
    queryFn: fetchRuntime,
    refetchInterval: 3000,
  });

  if (isLoading) {
    return (
      <div className="p-8 space-y-6">
        <h2 className="text-3xl font-bold tracking-tight mb-6">Runtime Monitoring</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
      </div>
    );
  }

  const { scheduler, pipeline, ui } = runtime || {};

  return (
    <div className="p-8 space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Runtime Monitoring</h2>
        <p className="text-muted-foreground">Live status of background processes.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Scheduler
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Status</span>
              <Badge variant={scheduler?.status === 'RUNNING' ? 'default' : scheduler?.status === 'STALE' ? 'destructive' : 'secondary'}>
                {scheduler?.status || 'UNKNOWN'}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Process Alive</span>
              <span>{scheduler?.is_alive ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">PID</span>
              <span className="font-mono text-sm">{scheduler?.pid || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Heartbeat Age</span>
              <span>{scheduler?.heartbeat_age ? `${Math.round(scheduler.heartbeat_age)}s` : 'N/A'}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Status</span>
              <Badge variant={pipeline?.status === 'RUNNING' ? 'default' : 'outline'}>
                {pipeline?.status || 'IDLE'}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Process Alive</span>
              <span>{pipeline?.is_alive ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">PID</span>
              <span className="font-mono text-sm">{pipeline?.pid || 'N/A'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Pipeline Lock</span>
              <Badge variant={scheduler?.lock ? 'destructive' : 'secondary'}>
                {scheduler?.lock ? 'LOCKED' : 'FREE'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5 text-primary" />
              UI Server
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">Status</span>
              <Badge variant="default">{ui?.status || 'ONLINE'}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-semibold text-muted-foreground">PID</span>
              <span className="font-mono text-sm">{ui?.pid || 'N/A'}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
