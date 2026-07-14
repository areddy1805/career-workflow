import { useEffect, useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { fetchJobDetails, transitionQueueJob } from '@/lib/api';
import { formatSalary } from '@/lib/utils';
import { Loader2, ExternalLink, CheckCircle, XCircle, Clock, Search } from 'lucide-react';

interface JobDrawerProps {
  jobId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTransitioned: () => void;
}

export function JobDrawer({ jobId, open, onOpenChange, onTransitioned }: JobDrawerProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (jobId && open) {
      setLoading(true);
      fetchJobDetails(jobId)
        .then(res => setData(res))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    } else {
      setData(null);
    }
  }, [jobId, open]);

  const handleTransition = async (status: string) => {
    if (!jobId) return;
    try {
      await transitionQueueJob(jobId, status, "From UI Drawer");
      onTransitioned();
      onOpenChange(false);
    } catch (e) {
      console.error(e);
    }
  };

  const getJobUrl = () => {
    const ov = data?.overview;
    if (!ov) return null;

    const url = ov.application_url || ov.apply_link || ov.url || ov.job_url || ov.original_job_url || ov.provider_url;

    if (url) {
      if (url.startsWith('http')) return url;
      if (url.startsWith('job-listings-') || url.startsWith('/job-listings-')) {
        return `https://www.naukri.com/${url.replace(/^\//, '')}`;
      }
    }

    return url || null;
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
               <Button variant="default" size="sm" onClick={() => handleTransition('APPLIED')} className="bg-green-600 hover:bg-green-700 text-white">
                 <CheckCircle className="w-4 h-4 mr-2" /> Mark Applied
               </Button>
               <Button variant="outline" size="sm" onClick={() => handleTransition('SKIPPED')} className="text-orange-600 border-orange-200 hover:bg-orange-50">
                 <Clock className="w-4 h-4 mr-2" /> Skip
               </Button>
               <Button variant="ghost" size="sm" onClick={() => handleTransition('DISMISSED')} className="text-red-600 hover:bg-red-50">
                 <XCircle className="w-4 h-4 mr-2" /> Dismiss
               </Button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm bg-muted/30 p-4 rounded-lg">
              <div><span className="font-semibold text-muted-foreground">Experience:</span> {data.overview?.experience || 'N/A'}</div>
              <div><span className="font-semibold text-muted-foreground">Salary:</span> {data.overview?.salary ? formatSalary(data.overview.salary) : 'N/A'}</div>
              <div><span className="font-semibold text-muted-foreground">AI Score:</span> {data.overview?.ai_score || data.overview?.score || 'N/A'}</div>
              <div>
                <span className="font-semibold text-muted-foreground">Source:</span>{' '}
                <span className="uppercase tracking-wide">
                  {data.overview?.provider ? data.overview.provider.replace('_', ' ') : (data.overview?.source || 'N/A')}
                </span>
              </div>
            </div>

            {(data.overview?.ai_reason || data.overview?.reason) && (
              <div className="bg-secondary/30 p-4 rounded-lg border border-secondary">
                <h4 className="font-semibold mb-2 flex items-center text-primary"><Search className="w-4 h-4 mr-2" /> AI Analysis</h4>
                <p className="text-sm leading-relaxed">{data.overview.ai_reason || data.overview.reason}</p>
              </div>
            )}

            {/* Provenance & Deduplication */}
            {data.overview?.provenance && (
              <div className="bg-muted/30 p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 border-b pb-1">Acquisition Provenance</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="font-medium text-muted-foreground">Generated Query:</span> {data.overview.provenance.generated_query || '-'}</div>
                  <div><span className="font-medium text-muted-foreground">Search Profile:</span> {data.overview.provenance.search_profile || '-'}</div>
                  <div><span className="font-medium text-muted-foreground">Matched Tech:</span> {data.overview.provenance.matched_technology || '-'}</div>
                  <div><span className="font-medium text-muted-foreground">Original Source:</span> {data.overview.provenance.provider || '-'}</div>
                </div>
                {data.overview.provenance.also_seen_on && data.overview.provenance.also_seen_on.length > 0 && (
                  <div className="mt-3 pt-2 border-t text-xs">
                    <span className="font-medium text-muted-foreground">Also discovered on: </span>
                    <span className="uppercase tracking-wide text-primary">
                      {data.overview.provenance.also_seen_on.join(', ')}
                    </span>
                  </div>
                )}
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
