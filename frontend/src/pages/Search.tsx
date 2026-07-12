import { useQuery } from '@tanstack/react-query';
import { fetchSearchIntelligence } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Globe, MapPin, Search as SearchIcon, Tag } from 'lucide-react';

export default function Search() {
  const { data, isLoading } = useQuery({
    queryKey: ['search_intelligence'],
    queryFn: fetchSearchIntelligence,
  });

  if (isLoading) {
    return <div className="p-6 text-muted-foreground">Loading search intelligence...</div>;
  }

  const { active_profiles = [], locations = [], total_queries = 0, queries = [] } = data || {};

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold text-lg tracking-tight flex items-center gap-2">
          <SearchIcon className="w-5 h-5 text-primary" />
          Search Intelligence Engine
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6 max-w-[1400px] mx-auto w-full">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Globe className="w-3.5 h-3.5" /> Active Profiles
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight">{active_profiles.length}</div>
              <div className="flex flex-wrap gap-1 mt-3">
                {active_profiles.map((p: string) => (
                  <Badge key={p} variant="secondary" className="text-[10px] uppercase font-mono">{p}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5" /> Locations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight">{locations.length}</div>
              <div className="flex flex-wrap gap-1 mt-3">
                {locations.map((loc: string) => (
                  <Badge key={loc} variant="outline" className="text-[10px]">{loc}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Tag className="w-3.5 h-3.5" /> Generated Queries
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight text-primary">{total_queries}</div>
              <p className="text-xs text-muted-foreground mt-1">Maximum deterministic combinations</p>
            </CardContent>
          </Card>
        </div>

        <Card className="shadow-none border-border/50">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Active Query Combinations</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground font-medium">
                  <tr>
                    <th className="px-4 py-2 font-medium">Query String</th>
                    <th className="px-4 py-2 font-medium">Location</th>
                    <th className="px-4 py-2 font-medium">Profile</th>
                    <th className="px-4 py-2 font-medium">Technology Match</th>
                    <th className="px-4 py-2 font-medium">Track</th>
                  </tr>
                </thead>
                <tbody>
                  {queries.map((q: any, i: number) => (
                    <tr key={i} className="border-b border-border/20 hover:bg-muted/30 last:border-0 transition-colors">
                      <td className="px-4 py-2 font-mono truncate max-w-[300px]" title={q.keyword}>{q.keyword}</td>
                      <td className="px-4 py-2 truncate max-w-[150px]">{q.location}</td>
                      <td className="px-4 py-2"><Badge variant="outline" className="text-[10px] uppercase">{q.search_profile}</Badge></td>
                      <td className="px-4 py-2 truncate max-w-[150px] text-muted-foreground">{q.matched_technology}</td>
                      <td className="px-4 py-2">{q.track}</td>
                    </tr>
                  ))}
                  {!queries.length && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No queries generated.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
