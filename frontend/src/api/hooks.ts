// TanStack Query hooks own all server state, polling and background refresh.
// Polling provides near-real-time refresh; `keepPreviousData` preserves the
// last successful response while a background refresh is in flight.

import { useQuery } from '@tanstack/react-query';

import { getJson } from './client';
import type {
  AlertsResponse,
  FilterOptions,
  Filters,
  MarketOverviewResponse,
  PositionsResponse,
  SummaryOut,
} from './types';

const POLL_MS = 30_000;
// The market page polls faster so synthetic prices visibly tick.
const MARKET_POLL_MS = 5_000;

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
