// TanStack Query hooks own all server state, polling and background refresh.
// Polling provides near-real-time refresh; `keepPreviousData` preserves the
// last successful response while a background refresh is in flight.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { getJson, postJson } from './client';
import type {
  AlertsResponse,
  FilterOptions,
  Filters,
  IngestionRunOut,
  IngestionRunsResponse,
  MarketHistoryResponse,
  MarketOverviewResponse,
  PositionsResponse,
  SummaryOut,
} from './types';

const POLL_MS = 30_000;
// Real market data is refreshed by the ingestion process (~1 min cadence), so
// the page reads the persisted snapshot every 15s rather than chasing ticks.
const MARKET_POLL_MS = 15_000;

export function useFilterOptions() {
  return useQuery({
    queryKey: ['filters'],
    queryFn: () => getJson<FilterOptions>('/filters'),
  });
}

export function useSummary(filters: Filters) {
  return useQuery({
    queryKey: ['summary', filters],
    queryFn: () => getJson<SummaryOut>('/summary', filters),
    refetchInterval: POLL_MS,
    keepPreviousData: true,
  });
}

export function usePositions(filters: Filters) {
  return useQuery({
    queryKey: ['positions', filters],
    queryFn: () => getJson<PositionsResponse>('/positions', filters),
    refetchInterval: POLL_MS,
    keepPreviousData: true,
  });
}

export function useAlerts(filters: Filters) {
  return useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => getJson<AlertsResponse>('/alerts', filters),
    refetchInterval: POLL_MS,
    keepPreviousData: true,
  });
}

export function useMarketOverview() {
  return useQuery({
    queryKey: ['market'],
    queryFn: () => getJson<MarketOverviewResponse>('/market'),
    refetchInterval: MARKET_POLL_MS,
    keepPreviousData: true,
  });
}

export function useMarketHistory(symbol: string | null, limit = 500) {
  return useQuery({
    queryKey: ['market-history', symbol, limit],
    queryFn: () =>
      getJson<MarketHistoryResponse>(
        `/market/history?symbol=${encodeURIComponent(symbol as string)}&limit=${limit}`,
      ),
    enabled: Boolean(symbol),
    refetchInterval: MARKET_POLL_MS,
    keepPreviousData: true,
  });
}

export function useIngestionRuns(limit = 5) {
  return useQuery({
    queryKey: ['ingestion-runs', limit],
    queryFn: () => getJson<IngestionRunsResponse>(`/ingestion-runs?limit=${limit}`),
    refetchInterval: POLL_MS,
    keepPreviousData: true,
  });
}

// Manual "Refresh now": triggers one ingestion cycle, then refreshes the views
// that depend on persisted data.
export function useIngest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => postJson<IngestionRunOut>('/market/ingest'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['market'] });
      queryClient.invalidateQueries({ queryKey: ['market-history'] });
      queryClient.invalidateQueries({ queryKey: ['ingestion-runs'] });
    },
  });
}
