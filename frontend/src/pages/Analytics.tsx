import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { BarChart2, Activity, Filter, Database, Search } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('funnel');

  const { data: funnelData, isLoading: isLoadingFunnel } = useQuery({
    queryKey: ['intelligence', 'pipeline_funnel'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/intelligence/pipeline_funnel');
      if (!res.ok) throw new Error('Failed to fetch funnel');
      return res.json();
    },
  });

  const { data: providerData, isLoading: isLoadingProvider } = useQuery({
    queryKey: ['intelligence', 'provider_quality'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/intelligence/provider_quality');
      if (!res.ok) throw new Error('Failed to fetch provider quality');
      return res.json();
    },
  });

  const { data: queryData, isLoading: isLoadingQuery } = useQuery({
    queryKey: ['intelligence', 'query_analytics'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/intelligence/query_analytics');
      if (!res.ok) throw new Error('Failed to fetch query analytics');
      return res.json();
    },
  });

  if (isLoadingFunnel) {
    return (
      <div className="h-full flex items-center justify-center bg-background">
        <div className="animate-pulse">Loading Intelligence Data...</div>
      </div>
    );
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'funnel':
        const funnel = funnelData?.data?.funnel;
        if (!funnel) return <div>No funnel data</div>;
        
        const chartData = [
          { stage: 'Acquired', count: funnel.acquired },
          { stage: 'Classified', count: funnel.classified },
          { stage: 'Selected', count: funnel.selected },
          { stage: 'Submitted', count: funnel.applications?.submitted || 0 }
        ];

        return (
          <div className="space-y-6">
            <div className="border border-border/50 rounded-md bg-card/30 flex flex-col p-4">
              <h3 className="font-semibold mb-4">Pipeline Funnel Math</h3>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ left: 50, right: 20, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                    <XAxis type="number" tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                    <YAxis dataKey="stage" type="category" width={100} tick={{ fontSize: 10, fill: 'hsl(var(--foreground))' }} />
                    <Tooltip 
                      cursor={{ fill: 'hsl(var(--muted)/0.5)' }}
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '4px', fontSize: '12px' }} 
                    />
                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 2, 2, 0]} maxBarSize={30} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="border border-border/50 rounded-md bg-card/30 flex flex-col p-4">
              <h3 className="font-semibold mb-4">Rejections Breakdown</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(funnel.rejections || {}).map(([reason, count]) => (
                  <div key={reason} className="p-3 bg-secondary/20 rounded border border-border/50">
                    <div className="text-xs text-muted-foreground mb-1">{reason}</div>
                    <div className="text-xl font-mono">{String(count)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
        
      case 'providers':
        const providers = providerData?.data || [];
        return (
          <div className="border border-border/50 rounded-md bg-card/30 p-4">
            <h3 className="font-semibold mb-4">Provider Quality Analytics</h3>
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-secondary/50">
                <tr>
                  <th className="px-4 py-2">Provider</th>
                  <th className="px-4 py-2 text-right">Discovered</th>
                  <th className="px-4 py-2 text-right">Selected</th>
                  <th className="px-4 py-2 text-right">Yield</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((p: any) => (
                  <tr key={p.provider} className="border-b border-border/50">
                    <td className="px-4 py-2 font-medium">{p.provider}</td>
                    <td className="px-4 py-2 text-right font-mono">{p.jobs_discovered}</td>
                    <td className="px-4 py-2 text-right font-mono">{p.selected_jobs}</td>
                    <td className="px-4 py-2 text-right font-mono">{p.yield_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'queries':
        const queries = queryData?.data || [];
        return (
          <div className="border border-border/50 rounded-md bg-card/30 p-4">
            <h3 className="font-semibold mb-4">Query Analytics</h3>
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-secondary/50">
                <tr>
                  <th className="px-4 py-2">Provider</th>
                  <th className="px-4 py-2">Query</th>
                  <th className="px-4 py-2 text-right">Returned</th>
                  <th className="px-4 py-2 text-right">Selected</th>
                </tr>
              </thead>
              <tbody>
                {queries.slice(0, 50).map((q: any, i: number) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="px-4 py-2 font-medium text-xs text-muted-foreground">{q.provider}</td>
                    <td className="px-4 py-2 font-mono text-xs">{q.query}</td>
                    <td className="px-4 py-2 text-right font-mono">{q.jobs_returned}</td>
                    <td className="px-4 py-2 text-right font-mono">{q.selected}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10 gap-4">
        <h2 className="font-semibold text-lg tracking-tight flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-primary" />
          Intelligence
        </h2>
        
        <div className="flex bg-secondary/50 p-1 rounded-lg ml-auto">
          <button 
            onClick={() => setActiveTab('funnel')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'funnel' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            <Filter className="w-3 h-3 inline mr-2"/>Funnel
          </button>
          <button 
            onClick={() => setActiveTab('providers')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'providers' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            <Database className="w-3 h-3 inline mr-2"/>Providers
          </button>
          <button 
            onClick={() => setActiveTab('queries')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === 'queries' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            <Search className="w-3 h-3 inline mr-2"/>Queries
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6 max-w-6xl mx-auto w-full">
        {renderTab()}
      </div>
    </div>
  );
}
