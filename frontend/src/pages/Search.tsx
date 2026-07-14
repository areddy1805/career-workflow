import { useQuery } from '@tanstack/react-query';
import { fetchSearchIntelligence, fetchProviders } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Globe, MapPin, Search as SearchIcon, Tag, Server,
  CheckCircle, XCircle, AlertTriangle, Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const HEALTH_STYLES: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  healthy:        { icon: <CheckCircle className="w-3.5 h-3.5" />, color: "text-emerald-500", label: "Healthy" },
  rate_limited:   { icon: <Clock className="w-3.5 h-3.5" />,       color: "text-amber-500",  label: "Rate Limited" },
  captcha:        { icon: <AlertTriangle className="w-3.5 h-3.5" />,color: "text-orange-500", label: "Captcha" },
  login_required: { icon: <AlertTriangle className="w-3.5 h-3.5" />,color: "text-yellow-500", label: "Login Req." },
  disabled:       { icon: <XCircle className="w-3.5 h-3.5" />,      color: "text-muted-foreground", label: "Disabled" },
  maintenance:    { icon: <AlertTriangle className="w-3.5 h-3.5" />,color: "text-blue-400",   label: "Maintenance" },
  unavailable:    { icon: <XCircle className="w-3.5 h-3.5" />,      color: "text-destructive", label: "Unavailable" },
};

export default function Search() {
  const { data, isLoading } = useQuery({
    queryKey: ['search_intelligence'],
    queryFn: fetchSearchIntelligence,
  });
  const { data: providerData } = useQuery({
    queryKey: ['providers'],
    queryFn: fetchProviders,
  });

  if (isLoading) {
    return <div className="p-6 text-muted-foreground">Loading search intelligence...</div>;
  }

  const {
    active_profiles = [], locations = [], total_queries = 0,
    queries = [], technology_profiles = {},
  } = data || {};

  const providers = providerData?.providers || [];
  const enabledProviders = providers.filter((p: any) => p.enabled);
  const techGroups = Object.entries(technology_profiles as Record<string, string[]>);

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="flex items-center px-6 py-4 border-b shrink-0 bg-background/95 backdrop-blur z-10">
        <h2 className="font-semibold text-lg tracking-tight flex items-center gap-2">
          <SearchIcon className="w-5 h-5 text-primary" />
          Search Intelligence Engine
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6 max-w-[1400px] mx-auto w-full">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

          <Card className="shadow-none border-border/50 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                <Server className="w-3.5 h-3.5" /> Active Providers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tracking-tight">{enabledProviders.length}</div>
              <div className="flex flex-wrap gap-1 mt-3">
                {enabledProviders.map((p: any) => (
                  <Badge key={p.name} variant="outline" className="text-[10px] uppercase">{p.name}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Technology Profile Breakdown */}
        {techGroups.length > 0 && (
          <Card className="shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Technology Profiles</CardTitle>
              <p className="text-xs text-muted-foreground">Query coverage by technology group</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {techGroups.map(([group, keywords]) => (
                  <div key={group} className="p-3 rounded-lg border border-border/50 bg-muted/20">
                    <div className="text-xs font-semibold uppercase tracking-wide text-foreground mb-2 flex items-center justify-between">
                      <span>{group}</span>
                      <Badge variant="secondary" className="text-[10px]">{keywords.length} queries</Badge>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {keywords.slice(0, 6).map((kw: string) => (
                        <Badge key={kw} variant="outline" className="text-[10px] font-mono truncate max-w-[160px]" title={kw}>
                          {kw}
                        </Badge>
                      ))}
                      {keywords.length > 6 && (
                        <span className="text-[10px] text-muted-foreground self-center">+{keywords.length - 6} more</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Provider Capability Matrix */}
        {providers.length > 0 && (
          <Card className="shadow-none border-border/50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Provider Capability Matrix</CardTitle>
              <p className="text-xs text-muted-foreground">Feature support across all configured providers</p>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground font-medium">
                    <tr>
                      <th className="px-4 py-2 font-medium">Provider</th>
                      <th className="px-4 py-2 font-medium text-center">Auto Apply</th>
                      <th className="px-4 py-2 font-medium text-center">Auth</th>
                      <th className="px-4 py-2 font-medium text-center">Pagination</th>
                      <th className="px-4 py-2 font-medium text-center">Location</th>
                      <th className="px-4 py-2 font-medium text-center">Remote</th>
                      <th className="px-4 py-2 font-medium text-center">Salary</th>
                      <th className="px-4 py-2 font-medium text-center">Experience</th>
                      <th className="px-4 py-2 font-medium text-center">Rate Limited</th>
                      <th className="px-4 py-2 font-medium text-center">Captcha Risk</th>
                      <th className="px-4 py-2 font-medium text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {providers.map((p: any) => {
                      const caps = p.capabilities || {};
                      const health = p.health;
                      const healthInfo = HEALTH_STYLES[health?.status || (p.enabled ? 'healthy' : 'disabled')];
                      return (
                        <tr key={p.name} className={cn(
                          "border-b border-border/20 hover:bg-muted/20 last:border-0 transition-colors",
                          !p.enabled && "opacity-50"
                        )}>
                          <td className="px-4 py-2">
                            <div className="font-semibold uppercase tracking-wide">{p.name}</div>
                            <div className="text-[10px] text-muted-foreground">{p.provider_type || 'job_board'}</div>
                          </td>
                          {[
                            caps.supports_auto_apply, caps.authentication_required, caps.supports_pagination,
                            caps.supports_location_filter, caps.supports_remote_filter, caps.supports_salary_filter,
                            caps.supports_experience_filter, caps.rate_limited, caps.captcha_risk,
                          ].map((val, i) => (
                            <td key={i} className="px-4 py-2 text-center">
                              <span className={val ? "text-emerald-500" : "text-muted-foreground/40"}>
                                {val ? "✓" : "✗"}
                              </span>
                            </td>
                          ))}
                          <td className="px-4 py-2 text-center">
                            {healthInfo ? (
                              <span className={cn("flex items-center justify-center gap-1", healthInfo.color)}>
                                {healthInfo.icon}
                                <span className="text-[10px]">{healthInfo.label}</span>
                              </span>
                            ) : (
                              <span className="text-muted-foreground text-[10px]">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Active Query Combinations */}
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
                    <th className="px-4 py-2 font-medium">Technology Group</th>
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
