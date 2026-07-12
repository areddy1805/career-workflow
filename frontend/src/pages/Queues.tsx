import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchManualQueues, fetchReviewQueue, fetchWorkflowQueue, transitionWorkflowQueue, addManualJob } from '@/lib/api';
import { UserPlus, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { CopyButton } from '@/components/CopyButton';

export default function Queues() {
  const [activeTab, setActiveTab] = useState<'manual' | 'review' | 'workflow'>('workflow');

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      {/* Top Action Bar */}
      <div className="flex justify-between items-center px-4 py-2 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <div className="flex items-center gap-6">
          <h2 className="font-semibold tracking-tight">Queues</h2>
          <div className="flex items-center gap-1 bg-muted p-0.5 rounded-md">
            <TabButton active={activeTab === 'workflow'} onClick={() => setActiveTab('workflow')}>Workflow Queue</TabButton>
            <TabButton active={activeTab === 'manual'} onClick={() => setActiveTab('manual')}>Manual Queue</TabButton>
            <TabButton active={activeTab === 'review'} onClick={() => setActiveTab('review')}>Review Queue</TabButton>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar p-4 md:p-6">
        {activeTab === 'workflow' && <WorkflowQueueView />}
        {activeTab === 'manual' && <ManualQueueView />}
        {activeTab === 'review' && <ReviewQueueView />}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean, onClick: () => void, children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1 text-xs font-medium rounded-sm transition-colors",
        active ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {children}
    </button>
  );
}

function WorkflowQueueView() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['workflow_queue'], queryFn: fetchWorkflowQueue });
  
  const transitionMutation = useMutation({
    mutationFn: (params: { jobId: string, toStatus: string }) => transitionWorkflowQueue(params.jobId, params.toStatus),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflow_queue'] })
  });

  if (isLoading) return <div className="text-muted-foreground">Loading workflow queue...</div>;

  return (
    <div className="flex flex-col gap-6 max-w-[1200px] mx-auto pb-20">
      <div className="flex flex-col gap-1">
        <h3 className="font-semibold">Workflow Analytics</h3>
        <p className="text-xs text-muted-foreground">Conversion funnel and queue health</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {data?.funnel?.map((step: any) => (
          <div key={step.status} className="border border-border/50 bg-card rounded-md p-3 flex flex-col justify-center">
            <span className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider mb-1">{step.status.replace(/_/g, ' ')}</span>
            <div className="flex items-end justify-between">
              <span className="font-semibold text-lg">{step.count}</span>
              <span className="text-xs text-primary">{step.conversion_rate_pct}%</span>
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-1 mt-4">
        <h3 className="font-semibold">Active Items</h3>
      </div>

      <div className="border border-border/50 bg-card rounded-md overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground font-medium">
            <tr>
              <th className="px-4 py-2 font-medium">Job ID</th>
              <th className="px-4 py-2 font-medium">Title</th>
              <th className="px-4 py-2 font-medium">Company</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.items?.map((item: any) => (
              <tr key={item.job_id} className="border-b border-border/20 hover:bg-muted/30 last:border-0 transition-colors">
                <td className="px-4 py-2 font-mono flex items-center gap-2"><CopyButton value={item.job_id} /> {item.job_id.substring(0, 8)}...</td>
                <td className="px-4 py-2 truncate max-w-[200px]">{item.title}</td>
                <td className="px-4 py-2 truncate max-w-[150px]">{item.company}</td>
                <td className="px-4 py-2"><Badge variant="outline" className="text-[10px] uppercase">{item.workflow_status}</Badge></td>
                <td className="px-4 py-2 text-right">
                  <select 
                    className="bg-background border border-border/50 rounded px-2 py-1 text-[10px] uppercase"
                    onChange={(e) => {
                      if (e.target.value) {
                        transitionMutation.mutate({ jobId: item.job_id, toStatus: e.target.value });
                        e.target.value = '';
                      }
                    }}
                    defaultValue=""
                  >
                    <option value="" disabled>Transition...</option>
                    <option value="VIEWED">Viewed</option>
                    <option value="SHORTLISTED">Shortlisted</option>
                    <option value="REJECTED">Rejected</option>
                    <option value="APPLIED">Applied</option>
                  </select>
                </td>
              </tr>
            ))}
            {!data?.items?.length && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">Queue is empty.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReviewQueueView() {
  const { data, isLoading } = useQuery({ queryKey: ['review_queue'], queryFn: fetchReviewQueue });

  if (isLoading) return <div className="text-muted-foreground">Loading review queue...</div>;

  return (
    <div className="flex flex-col gap-6 max-w-[1200px] mx-auto pb-20">
      <div className="flex flex-col gap-1">
        <h3 className="font-semibold">Review Queue</h3>
        <p className="text-xs text-muted-foreground">Jobs selected for application in the latest terminal run.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 w-64">
        <div className="border border-border/50 bg-card rounded-md p-3 flex flex-col justify-center">
          <span className="text-[10px] uppercase font-mono text-muted-foreground tracking-wider mb-1">Selected Jobs</span>
          <span className="font-semibold text-lg">{data?.length || 0}</span>
        </div>
      </div>

      <div className="border border-border/50 bg-card rounded-md overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground font-medium">
            <tr>
              <th className="px-4 py-2 font-medium">Job ID</th>
              <th className="px-4 py-2 font-medium">Title</th>
              <th className="px-4 py-2 font-medium">Company</th>
              <th className="px-4 py-2 font-medium">Score</th>
              <th className="px-4 py-2 font-medium">Priority</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((item: any) => (
              <tr key={item.job_id} className="border-b border-border/20 hover:bg-muted/30 last:border-0 transition-colors">
                <td className="px-4 py-2 font-mono flex items-center gap-2"><CopyButton value={item.job_id} /> {item.job_id.substring(0, 8)}...</td>
                <td className="px-4 py-2 truncate max-w-[250px]">{item.title}</td>
                <td className="px-4 py-2">{item.company}</td>
                <td className="px-4 py-2 font-mono text-primary">{item.score}</td>
                <td className="px-4 py-2"><Badge variant="outline" className="text-[10px] uppercase">{item.priority}</Badge></td>
              </tr>
            ))}
            {!data?.length && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No selected jobs in latest run.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ManualQueueView() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['manual_queue'], queryFn: fetchManualQueues });

  const addMutation = useMutation({
    mutationFn: addManualJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['manual_queue'] })
  });

  const [formData, setFormData] = useState({
    title: '', company: '', location: '', source: 'LinkedIn', source_url: '', priority: 'P2', notes: ''
  });

  if (isLoading) return <div className="text-muted-foreground">Loading manual queue...</div>;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addMutation.mutate(formData, {
      onSuccess: () => setFormData({ title: '', company: '', location: '', source: 'LinkedIn', source_url: '', priority: 'P2', notes: '' })
    });
  };

  return (
    <div className="flex flex-col xl:flex-row gap-6 max-w-[1600px] mx-auto pb-20">
      
      {/* Auto Detected */}
      <div className="flex-1 flex flex-col gap-6 min-w-0">
        <div className="flex flex-col gap-1">
          <h3 className="font-semibold flex items-center gap-2"><Activity className="w-4 h-4 text-primary" /> Auto Detected</h3>
          <p className="text-xs text-muted-foreground">External-apply jobs requiring manual action</p>
        </div>

        <div className="border border-border/50 bg-card rounded-md overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground font-medium">
              <tr>
                <th className="px-4 py-2 font-medium">Job ID</th>
                <th className="px-4 py-2 font-medium">Title</th>
                <th className="px-4 py-2 font-medium">Company</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.auto_detected?.map((item: any) => (
                <tr key={item.job_id} className="border-b border-border/20 hover:bg-muted/30 last:border-0 transition-colors">
                  <td className="px-4 py-2 font-mono flex items-center gap-2"><CopyButton value={item.job_id} /> {item.job_id.substring(0, 8)}...</td>
                  <td className="px-4 py-2 truncate max-w-[150px]">{item.title}</td>
                  <td className="px-4 py-2 truncate max-w-[150px]">{item.company}</td>
                  <td className="px-4 py-2"><Badge variant="outline" className="text-[10px] uppercase">{item.status || 'PENDING'}</Badge></td>
                </tr>
              ))}
              {!data?.auto_detected?.length && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">No external-apply jobs detected.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manually Sourced */}
      <div className="flex-[0.8] flex flex-col gap-6 min-w-0">
        <div className="flex flex-col gap-1">
          <h3 className="font-semibold flex items-center gap-2"><UserPlus className="w-4 h-4 text-primary" /> Manually Sourced</h3>
          <p className="text-xs text-muted-foreground">Jobs you found outside the automated pipeline</p>
        </div>

        <form onSubmit={handleSubmit} className="border border-border/50 bg-card rounded-md p-4 flex flex-col gap-4">
          <h4 className="text-sm font-semibold mb-2">Add Opportunity</h4>
          <div className="grid grid-cols-2 gap-3">
            <input required placeholder="Title" className="col-span-2 bg-background border border-border rounded px-3 py-1.5 text-xs" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
            <input required placeholder="Company" className="bg-background border border-border rounded px-3 py-1.5 text-xs" value={formData.company} onChange={e => setFormData({...formData, company: e.target.value})} />
            <input placeholder="Location" className="bg-background border border-border rounded px-3 py-1.5 text-xs" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} />
            <input required placeholder="Source URL" className="col-span-2 bg-background border border-border rounded px-3 py-1.5 text-xs" value={formData.source_url} onChange={e => setFormData({...formData, source_url: e.target.value})} />
            <select className="bg-background border border-border rounded px-3 py-1.5 text-xs" value={formData.priority} onChange={e => setFormData({...formData, priority: e.target.value})}>
              <option value="P1">P1</option>
              <option value="P2">P2</option>
              <option value="P3">P3</option>
            </select>
            <select className="bg-background border border-border rounded px-3 py-1.5 text-xs" value={formData.source} onChange={e => setFormData({...formData, source: e.target.value})}>
              <option value="LinkedIn">LinkedIn</option>
              <option value="Otta">Otta</option>
              <option value="Wellfound">Wellfound</option>
              <option value="Company">Company</option>
              <option value="Referral">Referral</option>
            </select>
            <textarea placeholder="Notes (optional)" className="col-span-2 bg-background border border-border rounded px-3 py-1.5 text-xs min-h-[60px]" value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} />
          </div>
          <button type="submit" disabled={addMutation.isPending} className="bg-primary text-primary-foreground font-semibold text-xs py-2 rounded shadow-sm hover:bg-primary/90 mt-2">
            {addMutation.isPending ? 'Saving...' : 'Save Job'}
          </button>
        </form>

        <div className="border border-border/50 bg-card rounded-md overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground font-medium">
              <tr>
                <th className="px-4 py-2 font-medium">Title</th>
                <th className="px-4 py-2 font-medium">Company</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.manual_sourced?.map((item: any) => (
                <tr key={item.id} className="border-b border-border/20 hover:bg-muted/30 last:border-0 transition-colors">
                  <td className="px-4 py-2 truncate max-w-[120px]">{item.title}</td>
                  <td className="px-4 py-2 truncate max-w-[120px]">{item.company}</td>
                  <td className="px-4 py-2"><Badge variant="outline" className="text-[10px] uppercase">{item.status || 'PENDING'}</Badge></td>
                </tr>
              ))}
              {!data?.manual_sourced?.length && (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">No manually sourced jobs.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
