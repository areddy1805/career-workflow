import { useQuery } from '@tanstack/react-query';
import { fetchRuns } from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { RelativeTime } from '@/components/RelativeTime';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CopyButton } from '@/components/CopyButton';

export default function Runs() {
  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
  });

  const [selectedRun, setSelectedRun] = useState<any | null>(null);

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      <div className="flex items-center px-4 py-2 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold tracking-tight">Runs Explorer</h2>
      </div>

      <div className="flex-1 overflow-auto bg-card">
        <Table>
          <TableHeader className="sticky top-0 bg-secondary border-b shadow-sm z-10">
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[200px]">Run ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead className="text-right">Acquired</TableHead>
              <TableHead className="text-right">Classified</TableHead>
              <TableHead className="text-right">Submitted</TableHead>
              <TableHead className="text-right">Failed</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={7}>
                    <div className="h-5 bg-muted animate-pulse rounded" />
                  </TableCell>
                </TableRow>
              ))
            ) : runs.length ? (
              runs.map((run: any) => (
                <TableRow 
                  key={run.run_id} 
                  className="cursor-pointer hover:bg-muted/50 transition-colors border-b border-border/40"
                  onClick={() => setSelectedRun(run)}
                >
                  <TableCell className="font-mono text-xs">{run.run_id}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`font-mono text-[10px] uppercase rounded-sm border px-1.5 
                      ${run.status === 'SUCCESS' ? 'text-green-500 border-green-500/20 bg-green-500/10' : 
                        run.status === 'FAILED' ? 'text-red-500 border-red-500/20 bg-red-500/10' : 
                        'text-muted-foreground border-border bg-muted/50'}`}>
                      {run.status}
                    </Badge>
                  </TableCell>
                  <TableCell><RelativeTime date={run.started_at} className="text-xs text-muted-foreground" /></TableCell>
                  <TableCell className="text-right font-mono">{run.acquired}</TableCell>
                  <TableCell className="text-right font-mono">{run.classified}</TableCell>
                  <TableCell className="text-right font-mono">{run.submitted}</TableCell>
                  <TableCell className={`text-right font-mono ${run.failed > 0 ? 'text-red-500 font-semibold' : ''}`}>{run.failed}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">No runs found.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Sheet open={!!selectedRun} onOpenChange={(open) => !open && setSelectedRun(null)}>
        <SheetContent className="w-[400px] sm:w-[500px] flex flex-col p-0 border-l border-border/50">
          <SheetHeader className="p-4 border-b bg-secondary/30">
            <div className="flex items-center justify-between">
              <SheetTitle className="text-base font-semibold">Run Details</SheetTitle>
              {selectedRun && <CopyButton value={selectedRun.run_id} />}
            </div>
            <p className="text-xs font-mono text-muted-foreground">{selectedRun?.run_id}</p>
          </SheetHeader>
          <ScrollArea className="flex-1 p-6">
            {selectedRun && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4 bg-muted/30 p-4 rounded-md border border-border/50">
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Status</p>
                    <Badge variant="outline" className="font-mono text-[10px]">{selectedRun.status}</Badge>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Started</p>
                    <RelativeTime date={selectedRun.started_at} className="text-xs" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Acquired</p>
                    <p className="font-mono">{selectedRun.acquired}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Classified</p>
                    <p className="font-mono">{selectedRun.classified}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Submitted</p>
                    <p className="font-mono">{selectedRun.submitted}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Failed</p>
                    <p className={`font-mono ${selectedRun.failed > 0 ? 'text-red-500 font-semibold' : ''}`}>{selectedRun.failed}</p>
                  </div>
                </div>
                {selectedRun.cache_metrics && Object.keys(selectedRun.cache_metrics).length > 0 && (
                  <div className="bg-muted/30 p-4 rounded-md border border-border/50">
                    <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-3 tracking-wider">Cache Performance</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-[10px] text-muted-foreground mb-1">LLM Hits / Misses</p>
                        <p className="font-mono text-xs">{selectedRun.cache_metrics.llm_hits} / {selectedRun.cache_metrics.llm_misses}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground mb-1">Embedding Hits / Misses</p>
                        <p className="font-mono text-xs">{selectedRun.cache_metrics.embedding_hits} / {selectedRun.cache_metrics.embedding_misses}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground mb-1">Detail Hits / Misses</p>
                        <p className="font-mono text-xs">{selectedRun.cache_metrics.detail_hits} / {selectedRun.cache_metrics.detail_misses}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground mb-1">HTTP Hits / Misses</p>
                        <p className="font-mono text-xs">{selectedRun.cache_metrics.http_hits} / {selectedRun.cache_metrics.http_misses}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground mb-1">Lookup Time</p>
                        <p className="font-mono text-xs">{selectedRun.cache_metrics.total_lookup_time_ms?.toFixed(1)}ms</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground mb-1">Save Time</p>
                        <p className="font-mono text-xs">{selectedRun.cache_metrics.total_save_time_ms?.toFixed(1)}ms</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </div>
  );
}
