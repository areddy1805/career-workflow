import { useEffect, useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQueryClient } from '@tanstack/react-query';
import { fetchJobDetails, transitionQueueJob } from '@/lib/api';
import { formatSalary, cn } from '@/lib/utils';
import { Loader2, ExternalLink, CheckCircle, XCircle, SkipForward, Search, AlertCircle } from 'lucide-react';

interface JobDrawerProps {
  jobId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTransitioned: () => void;
}

export function JobDrawer({ jobId, open, onOpenChange, onTransitioned }: JobDrawerProps) {
  const [loading, setLoading] = useState(false);
  const [transitioning, setTransitioning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (jobId && open) {
      setLoading(true);
      setError(null);
      fetchJobDetails(jobId)
        .then(res => setData(res))
        .catch(err => { console.error(err); setError('Failed to load job details.'); })
        .finally(() => setLoading(false));
    } else {
      setData(null);
      setError(null);
    }
  }, [jobId, open]);

  // WorkflowStatus valid values: NEW, PENDING, IN_PROGRESS, OPENED, APPLIED, INTERVIEW, OFFER, REJECTED, ARCHIVED
  // Skip → REJECTED (workflow machine maps this cleanly)
  // Dismiss → ARCHIVED (terminal state)
  const handleTransition = async (status: string) => {
    if (!jobId) return;
    setTransitioning(status);
    setError(null);
    try {
      await transitionQueueJob(jobId, status, 'From UI Drawer');
      // Invalidate all queue-related queries so the list refreshes
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      onTransitioned();
      onOpenChange(false);
    } catch (e: any) {
      console.error(e);
      setError(`Transition to ${status} failed — the current status may not allow this action.`);
    } finally {
      setTransitioning(null);
    }
  };

  const getJobUrl = () => {
    const url = data?.overview?.apply_link || data?.overview?.url || data?.overview?.source_url;
    if (!url) return null;
    if (url.startsWith('http')) return url;
    if (url.startsWith('job-listings-') || url.startsWith('/job-listings-')) {
      return `https://www.naukri.com/${url.replace(/^\//, '')}`;
    }
    return `https://www.naukri.com/job-listings-${url}`;
  };

  const jobUrl = getJobUrl();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto sm:w-[800px]">
        {loading || !data ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6">
            <SheetHeader>
              <div className="flex justify-between items-start gap-4">
                <div>
                  <SheetTitle className="text-2xl">{data.overview?.title}</SheetTitle>
                  <SheetDescription className="text-lg">
                    {data.overview?.company} • {data.overview?.location}
                  </SheetDescription>
                </div>
                <Badge variant="secondary" className="text-sm px-3 py-1 whitespace-nowrap">
                  {data.overview?.workflow_status || data.overview?.status}
                </Badge>
              </div>
            </SheetHeader>

            <div className="flex flex-wrap gap-2 border-b pb-4">
               {jobUrl ? (
                 <Button variant="outline" size="sm" onClick={() => window.open(jobUrl, '_blank')}>
                   <ExternalLink className="w-4 h-4 mr-2" /> Open Job
                 </Button>
               ) : null}
               {/* APPLIED is valid from: IN_PROGRESS, OPENED states */}
               <Button
                 variant="default" size="sm"
                 onClick={() => handleTransition('APPLIED')}
                 disabled={!!transitioning}
                 className="bg-green-600 hover:bg-green-700 text-white"
               >
                 {transitioning === 'APPLIED' ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                 Mark Applied
               </Button>
               {/* REJECTED is the correct status for skip/pass — valid from PENDING, IN_PROGRESS, OPENED, APPLIED, INTERVIEW */}
               <Button
                 variant="outline" size="sm"
                 onClick={() => handleTransition('REJECTED')}
                 disabled={!!transitioning}
                 className="text-orange-500 border-orange-500/30 hover:bg-orange-500/10 dark:hover:bg-orange-500/10"
               >
                 {transitioning === 'REJECTED' ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <SkipForward className="w-4 h-4 mr-2" />}
                 Skip
               </Button>
               {/* ARCHIVED is the terminal dismiss — valid from most states */}
               <Button
                 variant="ghost" size="sm"
                 onClick={() => handleTransition('ARCHIVED')}
                 disabled={!!transitioning}
                 className="text-destructive hover:bg-destructive/10"
               >
                 {transitioning === 'ARCHIVED' ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                 Dismiss
               </Button>
            </div>
            {error && (
              <div className="flex items-start gap-2 text-xs text-destructive bg-destructive/10 border border-destructive/20 rounded p-3">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm bg-muted/30 p-4 rounded-lg">
              <div><span className="font-semibold text-muted-foreground">Experience:</span> {data.overview?.experience || 'N/A'}</div>
              <div><span className="font-semibold text-muted-foreground">Salary:</span> {data.overview?.salary ? formatSalary(data.overview.salary) : 'N/A'}</div>
              <div><span className="font-semibold text-muted-foreground">AI Score:</span> {data.overview?.ai_score || data.overview?.score || 'N/A'}</div>
              <div><span className="font-semibold text-muted-foreground">Source:</span> {data.overview?.source || 'N/A'}</div>
            </div>

            {(data.overview?.ai_reason || data.overview?.reason) && (
              <div className="bg-secondary/30 p-4 rounded-lg border border-secondary">
                <h4 className="font-semibold mb-2 flex items-center text-primary"><Search className="w-4 h-4 mr-2" /> AI Analysis</h4>
                <p className="text-sm leading-relaxed">{data.overview.ai_reason || data.overview.reason}</p>
              </div>
            )}

            {data.events && data.events.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2 border-b pb-1">Application History</h4>
                <ul className="text-sm space-y-2">
                  {data.events.map((e: any, i: number) => (
                    <li key={i} className="flex gap-4 p-2 hover:bg-muted/50 rounded">
                      <span className="text-muted-foreground w-32 shrink-0">{new Date(e.timestamp).toLocaleString()}</span>
                      <span className="font-medium shrink-0 w-24">{e.status}</span>
                      {e.note && <span className="text-muted-foreground truncate">{e.note}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data.overview?.description && (
              <div>
                <h4 className="font-semibold mb-2 border-b pb-1">Job Description</h4>
                <div 
                  className="text-sm bg-muted/30 p-4 rounded-lg border max-h-[500px] overflow-y-auto [&>p]:mb-4 [&>ul]:list-disc [&>ul]:pl-5 [&>ul]:mb-4"
                  dangerouslySetInnerHTML={{ __html: data.overview.description }}
                />
              </div>
            )}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
