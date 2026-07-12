import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchJobs, fetchJobDetails } from '@/lib/api';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from '@tanstack/react-table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function Jobs() {
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: fetchJobs,
  });

  const [globalFilter, setGlobalFilter] = useState('');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const columns = [
    { accessorKey: 'status', header: 'Status', cell: ({ row }: any) => <Badge variant="outline">{row.getValue('status') || 'UNKNOWN'}</Badge> },
    { accessorKey: 'company', header: 'Company' },
    { accessorKey: 'title', header: 'Title' },
    { accessorKey: 'score', header: 'AI Score' },
    { accessorKey: 'location', header: 'Location' },
    { accessorKey: 'source', header: 'Source' },
    { accessorKey: 'last_updated_at', header: 'Updated', cell: ({ row }: any) => new Date(row.getValue('last_updated_at')).toLocaleDateString() },
  ];

  const table = useReactTable({
    data: jobs,
    columns,
    state: { globalFilter },
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const { data: jobDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => fetchJobDetails(selectedJobId!),
    enabled: !!selectedJobId,
  });

  return (
    <div className="p-8 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold tracking-tight">Job Explorer</h2>
        <Input
          placeholder="Search jobs..."
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="rounded-md border flex-1 overflow-auto bg-card">
        <Table>
          <TableHeader className="sticky top-0 bg-secondary/80 backdrop-blur">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  onClick={() => setSelectedJobId((row.original as any).job_id)}
                  className="cursor-pointer hover:bg-muted/50"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  {isLoading ? 'Loading jobs...' : 'No jobs found.'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Sheet open={!!selectedJobId} onOpenChange={(open) => !open && setSelectedJobId(null)}>
        <SheetContent className="w-[400px] sm:w-[600px] sm:max-w-[800px] overflow-hidden flex flex-col">
          <SheetHeader>
            <SheetTitle>{jobDetails?.overview?.title || 'Job Details'}</SheetTitle>
            <SheetDescription>
              {jobDetails?.overview?.company} - {jobDetails?.overview?.location}
            </SheetDescription>
          </SheetHeader>
          <ScrollArea className="flex-1 mt-6 border-t pt-4">
            {detailsLoading ? (
              <div className="space-y-4 p-4">
                <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                <div className="h-4 w-1/2 bg-muted animate-pulse rounded" />
              </div>
            ) : jobDetails ? (
              <div className="space-y-6 pb-8">
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wider mb-2">Overview</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Status</p>
                      <p className="font-medium">{jobDetails.overview.status || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">AI Score</p>
                      <p className="font-medium">{jobDetails.overview.score || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Priority</p>
                      <p className="font-medium">{jobDetails.overview.priority || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Source</p>
                      <p className="font-medium">{jobDetails.overview.source || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wider mb-2">History Events</h4>
                  {jobDetails.events?.length ? (
                    <div className="space-y-3">
                      {jobDetails.events.map((evt: any) => (
                        <div key={evt.id} className="text-sm border-l-2 border-primary pl-3 py-1">
                          <p className="font-semibold">{evt.status}</p>
                          <p className="text-muted-foreground text-xs">{new Date(evt.created_at).toLocaleString()}</p>
                          {evt.detail && <p className="mt-1 bg-muted p-2 rounded text-xs break-all">{evt.detail}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No events recorded.</p>
                  )}
                </div>

                <div className="pt-4 flex gap-2">
                  <Button variant="outline" onClick={() => navigator.clipboard.writeText(jobDetails.overview.job_id)}>Copy ID</Button>
                </div>
              </div>
            ) : null}
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </div>
  );
}
