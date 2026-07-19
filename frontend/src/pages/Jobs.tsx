import { useMemo, useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchJobs, fetchJobDetails } from '@/lib/api';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnResizeMode,
  RowSelectionState,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ContextMenu, ContextMenuContent, ContextMenuItem, ContextMenuTrigger, ContextMenuSeparator, ContextMenuSub, ContextMenuSubTrigger, ContextMenuSubContent } from '@/components/ui/context-menu';
import { Copy, X, Settings2, EyeOff, LayoutTemplate, ExternalLink } from 'lucide-react';
import { useJobStore } from '@/store/jobs';
import { Checkbox } from '@/components/ui/checkbox';
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { CopyButton } from '@/components/CopyButton';
import { RelativeTime } from '@/components/RelativeTime';

export default function Jobs() {
  const { data: jobs = [], isLoading } = useQuery({ queryKey: ['jobs'], queryFn: fetchJobs });
  
  // Persisted state
  const { sorting, columnVisibility, setSorting, setColumnVisibility } = useJobStore();
  
  // Local state
  const [globalFilter, setGlobalFilter] = useState('');
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  
  // Query for details
  const { data: jobDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['job', selectedJobId],
    queryFn: () => fetchJobDetails(selectedJobId!),
    enabled: !!selectedJobId,
  });

  const columns = useMemo(() => [
    {
      id: 'select',
      header: ({ table }: any) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
          className="translate-y-[2px]"
        />
      ),
      cell: ({ row }: any) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
          className="translate-y-[2px]"
        />
      ),
      size: 40,
      enableSorting: false,
      enableResizing: false,
    },
    { 
      accessorKey: 'status', 
      header: 'Status', 
      size: 100,
      cell: ({ row }: any) => {
        const status = row.getValue('status');
        const color = status === 'APPLIED' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' : 
                      status === 'REJECTED' ? 'bg-red-500/10 text-red-500 border-red-500/20' : 
                      'bg-primary/10 text-primary border-primary/20';
        return <Badge variant="outline" className={`font-mono text-[10px] uppercase rounded-sm border px-1.5 ${color}`}>{status || 'UNKNOWN'}</Badge>;
      } 
    },
    { accessorKey: 'company', header: 'Company', size: 150 },
    { accessorKey: 'title', header: 'Title', size: 250 },
    { accessorKey: 'score', header: 'Score', size: 80, cell: ({ row }: any) => <span className="font-mono">{row.getValue('score')}</span> },
    { accessorKey: 'location', header: 'Location', size: 150 },
    { accessorKey: 'source', header: 'Source', size: 120, cell: ({ row }: any) => <Badge variant="secondary" className="rounded-sm font-mono text-[10px]">{row.getValue('source')}</Badge> },
    { 
      accessorKey: 'last_updated_at', 
      header: 'Updated', 
      size: 150, 
      cell: ({ row }: any) => <RelativeTime date={row.getValue('last_updated_at')} className="text-muted-foreground text-xs" /> 
    },
    {
      id: 'actions',
      header: '',
      size: 60,
      enableSorting: false,
      enableResizing: false,
      cell: ({ row }: any) => {
        const url = (row.original as any).apply_url || (row.original as any).apply_link || (row.original as any).url || (row.original as any).source_url;
        if (!url) return null;
        return (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-muted-foreground hover:text-primary"
            onClick={(e) => { e.stopPropagation(); window.open(url, '_blank'); }}
            title="Open External"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        );
      }
    },
  ], []);

  const table = useReactTable({
    data: jobs,
    columns,
    state: { sorting, columnVisibility, globalFilter, rowSelection },
    enableRowSelection: true,
    columnResizeMode: 'onChange' as ColumnResizeMode,
    onSortingChange: setSorting as any,
    onColumnVisibilityChange: setColumnVisibility as any,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const { rows } = table.getRowModel();
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 36, // Dense rows
    overscan: 20,
  });

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedJobId || !rows.length) return;
      const currentIndex = rows.findIndex(r => (r.original as any).job_id === selectedJobId);
      if (e.key === 'ArrowDown' && currentIndex < rows.length - 1) {
        e.preventDefault();
        setSelectedJobId((rows[currentIndex + 1].original as any).job_id);
      } else if (e.key === 'ArrowUp' && currentIndex > 0) {
        e.preventDefault();
        setSelectedJobId((rows[currentIndex - 1].original as any).job_id);
      } else if (e.key === 'Escape') {
        setSelectedJobId(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedJobId, rows]);

  return (
    <div className="h-full flex flex-col bg-background text-sm">
      {/* Top Action Bar */}
      <div className="flex justify-between items-center px-4 py-2 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <div className="flex items-center gap-4">
          <h2 className="font-semibold tracking-tight">Job Explorer</h2>
          <Input
            placeholder="Filter jobs..."
            value={globalFilter ?? ''}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="h-7 w-64 text-xs bg-muted/50 focus-visible:bg-background"
          />
        </div>
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-7 text-xs gap-2">
                <Settings2 className="h-3 w-3" /> View
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48 text-xs">
              {table.getAllLeafColumns().map(column => {
                if (column.id === 'select') return null;
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) => column.toggleVisibility(!!value)}
                    className="text-xs"
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                );
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          {/* Data Grid Panel */}
          <ResizablePanel defaultSize={selectedJobId ? 60 : 100} minSize={30} className="relative flex flex-col bg-card transition-all duration-200">
            <div ref={parentRef} className="flex-1 overflow-auto custom-scrollbar relative">
              <div style={{ height: `${virtualizer.getTotalSize()}px`, width: table.getTotalSize(), position: 'relative' }}>
                {/* Headers */}
                <div className="sticky top-0 z-20 bg-secondary border-b flex text-xs font-medium text-muted-foreground">
                  {table.getHeaderGroups().map(headerGroup => (
                    <div key={headerGroup.id} className="flex w-full">
                      {headerGroup.headers.map(header => (
                        <div
                          key={header.id}
                          style={{ width: header.getSize() }}
                          className={`flex items-center px-3 py-1.5 border-r border-border/50 relative group ${header.id === 'select' ? 'sticky left-0 bg-secondary z-30' : ''}`}
                        >
                          <div 
                            className="flex-1 truncate cursor-pointer select-none" 
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {{ asc: ' ↑', desc: ' ↓' }[header.column.getIsSorted() as string] ?? null}
                          </div>
                          {header.column.getCanResize() && (
                            <div
                              onMouseDown={header.getResizeHandler()}
                              onTouchStart={header.getResizeHandler()}
                              className={`absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-primary/50 ${header.column.getIsResizing() ? 'bg-primary' : ''}`}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>

                {/* Rows */}
                {virtualizer.getVirtualItems().map(virtualRow => {
                  const row = rows[virtualRow.index];
                  const isSelected = (row.original as any).job_id === selectedJobId;
                  const isChecked = row.getIsSelected();

                  return (
                    <ContextMenu key={row.id}>
                      <ContextMenuTrigger asChild>
                        <div
                          style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: `${virtualRow.size}px`,
                            transform: `translateY(${virtualRow.start}px)`,
                          }}
                          className={`flex border-b border-border/40 transition-colors cursor-default
                            ${isSelected ? 'bg-primary/10 hover:bg-primary/15' : 'hover:bg-muted/50'}
                            ${isChecked ? 'bg-primary/5' : ''}
                          `}
                          onClick={() => setSelectedJobId((row.original as any).job_id)}
                        >
                          {row.getVisibleCells().map(cell => (
                            <div
                              key={cell.id}
                              style={{ width: cell.column.getSize() }}
                              className={`flex items-center px-3 truncate ${cell.column.id === 'select' ? 'sticky left-0 bg-inherit z-10' : ''}`}
                            >
                              {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </div>
                          ))}
                        </div>
                      </ContextMenuTrigger>
                      <ContextMenuContent className="w-48">
                        <ContextMenuItem onClick={() => navigator.clipboard.writeText((row.original as any).job_id)}>
                          <Copy className="w-3 h-3 mr-2" /> Copy Job ID
                        </ContextMenuItem>
                        <ContextMenuItem onClick={() => {
                          const url = (row.original as any).apply_url || (row.original as any).apply_link || (row.original as any).url || (row.original as any).source_url;
                          if (url) window.open(url, '_blank');
                        }}>
                          Open External
                        </ContextMenuItem>
                        <ContextMenuSeparator />
                        <ContextMenuSub>
                          <ContextMenuSubTrigger>Change Status</ContextMenuSubTrigger>
                          <ContextMenuSubContent className="w-32">
                            <ContextMenuItem>Set APPLIED</ContextMenuItem>
                            <ContextMenuItem>Set REJECTED</ContextMenuItem>
                            <ContextMenuItem>Set VIEWED</ContextMenuItem>
                          </ContextMenuSubContent>
                        </ContextMenuSub>
                        <ContextMenuSeparator />
                        <ContextMenuItem className="text-destructive"><EyeOff className="w-3 h-3 mr-2" /> Hide Job</ContextMenuItem>
                      </ContextMenuContent>
                    </ContextMenu>
                  );
                })}
              </div>
            </div>
            {isLoading && (
              <div className="absolute inset-0 bg-background/50 backdrop-blur-sm flex items-center justify-center z-50">
                <div className="flex items-center gap-2 text-sm text-muted-foreground font-mono bg-card px-4 py-2 border rounded-full shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  Loading...
                </div>
              </div>
            )}
          </ResizablePanel>

          {/* Job Details Drawer / Panel */}
          {selectedJobId && (
            <>
              <ResizableHandle withHandle className="bg-border/50 hover:bg-primary/50 transition-colors w-1" />
              <ResizablePanel defaultSize={40} minSize={25} maxSize={60} className="bg-card border-l flex flex-col relative z-20 shadow-[-10px_0_15px_-3px_rgba(0,0,0,0.1)]">
                <div className="h-12 border-b flex items-center justify-between px-4 bg-secondary/30 shrink-0">
                  <div className="flex items-center gap-2">
                    <LayoutTemplate className="w-4 h-4 text-muted-foreground" />
                    <span className="font-semibold text-sm">Job Details</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <CopyButton value={selectedJobId} />
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setSelectedJobId(null)}>
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                <ScrollArea className="flex-1">
                  {detailsLoading ? (
                    <div className="p-6 space-y-6">
                      <div className="space-y-2">
                        <div className="h-5 w-3/4 bg-muted animate-pulse rounded" />
                        <div className="h-4 w-1/2 bg-muted animate-pulse rounded" />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        {[1, 2, 3, 4].map((_, idx) => (
                          <div key={idx} className="space-y-1">
                            <div className="h-3 w-1/3 bg-muted animate-pulse rounded" />
                            <div className="h-4 w-2/3 bg-muted animate-pulse rounded" />
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : jobDetails ? (
                    <div className="p-6 space-y-8">
                      {/* Header Section */}
                      <div>
                        <h1 className="text-xl font-bold tracking-tight mb-1">{jobDetails.overview.title}</h1>
                        <p className="text-sm text-muted-foreground flex items-center gap-2">
                          <span className="font-medium text-foreground">{jobDetails.overview.company}</span>
                          <span>•</span>
                          <span>{jobDetails.overview.location}</span>
                        </p>
                      </div>

                      {/* Metadata Grid */}
                      <div className="grid grid-cols-2 gap-x-6 gap-y-4 bg-muted/30 p-4 rounded-md border border-border/50">
                        <div>
                          <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Status</p>
                          <Badge variant="outline" className="font-mono text-[10px]">{jobDetails.overview.status}</Badge>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">AI Score</p>
                          <p className="font-mono font-medium text-primary">{jobDetails.overview.score}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Priority</p>
                          <p className="text-sm">{jobDetails.overview.priority}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-semibold text-muted-foreground mb-1 tracking-wider">Source</p>
                          <p className="text-sm">{jobDetails.overview.source}</p>
                        </div>
                      </div>

                      {/* Timeline Events */}
                      <div>
                        <h4 className="text-[10px] uppercase font-semibold text-muted-foreground mb-3 tracking-wider">Execution Timeline</h4>
                        <div className="space-y-0 relative before:absolute before:inset-0 before:ml-[5px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
                          {jobDetails.events?.map((evt: any) => (
                            <div key={evt.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active py-2">
                              <div className="flex items-center justify-center w-3 h-3 rounded-full border border-background bg-primary shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 ml-0.5" />
                              <div className="w-[calc(100%-2rem)] md:w-[calc(50%-2rem)] bg-card border border-border/50 p-3 rounded-md shadow-sm ml-4 md:ml-0">
                                <div className="flex justify-between items-center mb-1">
                                  <span className="font-semibold text-xs text-primary">{evt.status}</span>
                                  <RelativeTime date={evt.created_at} className="text-[10px] text-muted-foreground" />
                                </div>
                                {evt.detail && <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{evt.detail}</p>}
                              </div>
                            </div>
                          ))}
                          {!jobDetails.events?.length && <p className="text-xs text-muted-foreground pl-4 border-l-2 border-border/50">No timeline events recorded.</p>}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-6 text-center text-sm text-muted-foreground">Failed to load details.</div>
                  )}
                </ScrollArea>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
      </div>
    </div>
  );
}
