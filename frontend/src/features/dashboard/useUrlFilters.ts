// Filters live in the URL query string so a filtered view is bookmarkable and
// shareable. This keeps a single source of truth for the active filters
// without pulling in a router for the current single-page dashboard.

import { useState } from 'react';

import type { Filters } from '../../api/types';

function readFromUrl(): Filters {
  const params = new URLSearchParams(window.location.search);
  return {
    desks: params.getAll('desk'),
    traders: params.getAll('trader'),
    commodities: params.getAll('commodity'),
  };
}

function writeToUrl(filters: Filters): void {
  const params = new URLSearchParams();
  filters.desks.forEach((d) => params.append('desk', d));
  filters.traders.forEach((t) => params.append('trader', t));
  filters.commodities.forEach((c) => params.append('commodity', c));
  const query = params.toString();
  const url = query ? `${window.location.pathname}?${query}` : window.location.pathname;
  window.history.replaceState(null, '', url);
}

export function useUrlFilters(): [Filters, (filters: Filters) => void] {
  const [filters, setFiltersState] = useState<Filters>(readFromUrl);

  const setFilters = (next: Filters): void => {
    setFiltersState(next);
    writeToUrl(next);
  };

  return [filters, setFilters];
}
