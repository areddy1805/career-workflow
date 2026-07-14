import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  fetchManualReviewQueue,
  fetchExternalApplyQueue,
  fetchOtherActionQueue
} from '@/lib/api';
import { cn, formatSalary } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { JobDrawer } from '@/components/JobDrawer';
import { ExternalLink, Search, Clock, ListChecks, CheckCircle, Copy, Globe, Building2 } from 'lucide-react';

// Provider badge color map
const PROVIDER_COLORS: Record<string, string> = {
  naukri:        'bg-purple-500/10 text-purple-400 border-purple-500/20',
  google_jobs:   'bg-blue-500/10 text-blue-400 border-blue-500/20',
  remoteok:      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  weworkremotely:'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  wellfound:     'bg-orange-500/10 text-orange-400 border-orange-500/20',
  instahyre:     'bg-rose-500/10 text-rose-400 border-rose-500/20',
  foundit:       'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
};

export default function Queues() {
  const [activeTab, setActiveTab] = useState<'manual-review' | 'external-apply' | 'other-action'>('manual-review');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const handleJobClick = (jobId: string) => {
    setSelectedJobId(jobId);
  };

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      {/* Top Action Bar */}
      <div className="flex justify-between items-center px-4 py-2 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <div className="flex items-center gap-6">
          <h2 className="font-semibold tracking-tight">Operator Inbox</h2>
          <div className="flex items-center gap-1 bg-muted p-0.5 rounded-md">
            <TabButton
              active={activeTab === 'manual-review'}
              onClick={() => setActiveTab('manual-review')}
              icon={<Search className="w-3.5 h-3.5" />}
            >
              Manual Review
            </TabButton>
            <TabButton
              active={activeTab === 'external-apply'}
              onClick={() => setActiveTab('external-apply')}
              icon={<ExternalLink className="w-3.5 h-3.5" />}
            >
              External Apply
            </TabButton>
            <TabButton
              active={activeTab === 'other-action'}
              onClick={() => setActiveTab('other-action')}
              icon={<ListChecks className="w-3.5 h-3.5" />}
            >
              Other Action Required
            </TabButton>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar p-4 md:p-6 bg-muted/10">
        <div className="max-w-[1400px] mx-auto">
          {activeTab === 'manual-review' && <QueueView type="manual-review" onRowClick={handleJobClick} />}
          {activeTab === 'external-apply' && <QueueView type="external-apply" onRowClick={handleJobClick} showProviderColumns />}
          {activeTab === 'other-action' && <QueueView type="other-action" onRowClick={handleJobClick} />}
        </div>
      </div>

      <JobDrawer
        jobId={selectedJobId}
        open={!!selectedJobId}
        onOpenChange={(open) => !open && setSelectedJobId(null)}
        onTransitioned={() => {}}
      />
    </div>
  );
}

function TabButton({ active, onClick, children, icon }: { active: boolean, onClick: () => void, children: React.ReactNode, icon?: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-sm transition-colors",
        active ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {icon}
      {children}
    </button>
  );
}

function ProviderBadge({ provider }: { provider: string }) {
  const classes = PROVIDER_COLORS[provider] || 'bg-muted text-muted-foreground border-border';
  return (
    <span className={cn("inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wide", classes)}>
      {provider?.replace('_', ' ')}
    </span>
  );
}

function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);
  const copy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  };
  return (
    <button
      onClick={copy}
      title={`Copy ${label}`}
      className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
    >
      {copied ? <CheckCircle className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
      {label}
    </button>
  );
}

function LinkButton({ url, label, icon }: { url: string; label: string; icon: React.ReactNode }) {
  if (!url) return null;
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className="flex items-center gap-1 text-[10px] text-primary hover:underline"
    >
      {icon}
      {label}
    </a>
  );
}

function QueueView({
  type,
  onRowClick,
  showProviderColumns = false,
}: {
  type: 'manual-review' | 'external-apply' | 'other-action';
  onRowClick: (id: string) => void;
  showProviderColumns?: boolean;
}) {
  const fetchFn = type === 'manual-review' ? fetchManualReviewQueue
    : type === 'external-apply' ? fetchExternalApplyQueue
    : fetchOtherActionQueue;

  const { data, isLoading } = useQuery({
    queryKey: ['queue', type],
    queryFn: fetchFn
  });

  if (isLoading) {
    return <div className="text-muted-foreground flex items-center gap-2"><Clock className="w-4 h-4 animate-pulse" /> Loading inbox...</div>;
  }

  const items = data?.items || [];

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground border border-dashed rounded-lg bg-background">
        <CheckCircle className="w-8 h-8 mb-3 opacity-20" />
        <p>Inbox zero. You are all caught up.</p>
      </div>
    );
  }

  return (
    <div className="bg-background border rounded-lg overflow-hidden shadow-sm">
      <table className="w-full text-left text-xs">
        <thead className="bg-muted/50 border-b text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium w-1/4">Company &amp; Role</th>
            <th className="px-4 py-3 font-medium w-32">Details</th>
            <th className="px-4 py-3 font-medium w-24">Score</th>
            {showProviderColumns ? (
              <>
                <th className="px-4 py-3 font-medium w-28">Source</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </>
            ) : (
              <th className="px-4 py-3 font-medium">Context / Reason</th>
            )}
            <th className="px-4 py-3 font-medium w-32 text-right">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item: any) => (
            <tr
              key={item.job_id}
              onClick={() => onRowClick(item.job_id)}
              className="border-b hover:bg-muted/30 cursor-pointer transition-colors group last:border-0"
            >
              <td className="px-4 py-3 align-top">
                <div className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">{item.title}</div>
                <div className="text-muted-foreground mt-0.5">{item.company}</div>
                <div className="text-[10px] text-muted-foreground/70 mt-1">{item.location || 'Unknown Location'}</div>
              </td>
              <td className="px-4 py-3 align-top space-y-1 text-muted-foreground">
                {item.experience && <div>Exp: <span className="font-medium text-foreground">{item.experience}</span></div>}
                {item.salary && <div>Pay: <span className="font-medium text-foreground">{formatSalary(item.salary)}</span></div>}
                {item.posted_date && <div>Posted: <span className="font-medium text-foreground">{item.posted_date}</span></div>}
              </td>
              <td className="px-4 py-3 align-top">
                {item.ai_score || item.score ? (
                  <Badge variant={Number(item.ai_score || item.score) >= 70 ? 'default' : 'secondary'}>
                    {item.ai_score || item.score} / 100
                  </Badge>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </td>

              {showProviderColumns ? (
                <>
                  {/* Apply Source */}
                  <td className="px-4 py-3 align-top">
                    {item.provider && <ProviderBadge provider={item.provider} />}
                    {item.apply_source && item.apply_source !== item.provider && (
                      <div className="text-[10px] text-muted-foreground mt-1">{item.apply_source}</div>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3 align-top" onClick={(e) => e.stopPropagation()}>
                    <div className="flex flex-col gap-1.5">
                      <LinkButton
                        url={item.original_job_url || item.url || ''}
                        label="Open Posting"
                        icon={<Globe className="w-3 h-3" />}
                      />
                      <LinkButton
                        url={item.url || item.application_url || ''}
                        label="Apply Now"
                        icon={<ExternalLink className="w-3 h-3" />}
                      />
                      {item.url && <CopyButton value={item.url} label="Copy URL" />}
                      {item.provider_job_id && item.provider_job_id !== item.job_id && (
                        <CopyButton value={item.provider_job_id} label="Copy Provider ID" />
                      )}
                      {item.job_id && <CopyButton value={item.job_id} label="Copy Job ID" />}
                    </div>
                  </td>
                </>
              ) : (
                <td className="px-4 py-3 align-top text-muted-foreground line-clamp-3">
                  {item.ai_reason || item.reason || item.notes?.[0] || 'Requires attention.'}
                </td>
              )}

              <td className="px-4 py-3 align-top text-right">
                <Badge variant="outline" className="uppercase text-[10px]">
                  {item.workflow_status || item.status}
                </Badge>
                <div className="text-[10px] text-muted-foreground mt-2">
                  {new Date(item.updated_at || item.created_at).toLocaleDateString()}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
