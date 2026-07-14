import { useQuery } from '@tanstack/react-query';
import { CheckCircle, AlertTriangle, Clock, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Providers() {
  const { data: providers, isLoading, error } = useQuery({
    queryKey: ['providers'],
    queryFn: () => fetch('/api/providers').then((r: Response) => r.json()).then((r: any) => r.providers || r.data || r)
  });

  const getLifecycleColor = (state: string) => {
    switch(state) {
      case 'production': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'experimental': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'disabled': return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
      case 'deprecated': return 'bg-red-500/10 text-red-500 border-red-500/20';
      default: return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
  };

  if (isLoading) return <div className="p-8 text-center text-muted-foreground"><RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />Loading providers...</div>;
  if (error) return <div className="p-8 text-red-500">Error loading providers</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Providers</h1>
          <p className="text-muted-foreground text-sm">Manage and monitor job acquisition sources.</p>
        </div>
      </div>

      <div className="border rounded-lg bg-card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-secondary/50 text-muted-foreground border-b">
            <tr>
              <th className="px-4 py-3 font-medium">Provider</th>
              <th className="px-4 py-3 font-medium">State</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Priority</th>
              <th className="px-4 py-3 font-medium">Health</th>
              <th className="px-4 py-3 font-medium">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {providers?.map((p: any) => (
              <tr key={p.name} className="hover:bg-secondary/30 transition-colors">
                <td className="px-4 py-3 font-medium flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary uppercase">
                    {p.name.slice(0, 2)}
                  </div>
                  {p.name}
                </td>
                <td className="px-4 py-3">
                  <span className={cn("px-2 py-0.5 rounded text-[10px] uppercase font-semibold border", getLifecycleColor(p.lifecycle_state || 'production'))}>
                    {p.lifecycle_state || 'production'}
                  </span>
                </td>
                <td className="px-4 py-3 text-muted-foreground capitalize">{p.provider_type}</td>
                <td className="px-4 py-3">{p.priority}</td>
                <td className="px-4 py-3">
                  {p.health ? (
                    <div className="flex items-center gap-1.5">
                      {p.health.status === 'healthy' ? <CheckCircle className="w-4 h-4 text-green-500" /> : <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                      <span className="capitalize">{p.health.status.replace('_', ' ')}</span>
                    </div>
                  ) : <span className="text-muted-foreground">Unknown</span>}
                </td>
                <td className="px-4 py-3 text-muted-foreground flex items-center gap-1.5">
                  <Clock className="w-3 h-3" />
                  {p.health?.latency_ms ? `${p.health.latency_ms.toFixed(0)}ms` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
