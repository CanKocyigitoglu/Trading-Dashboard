import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

// The full App imports Plotly transitively (dashboard + market charts), whose
// bundle touches canvas/URL APIs jsdom lacks. Charts aren't exercised by a
// navigation test, so stub Plotly to keep this suite about routing only.
vi.mock('plotly.js-dist-min', () => ({ default: {} }));
vi.mock('react-plotly.js/factory', () => ({ default: () => () => null }));

import { App } from '../App';

// Renders the real App (with its <Routes>) inside a MemoryRouter — main.tsx
// owns the BrowserRouter, so tests supply their own router without nesting two.
// retry:false keeps failed background queries (no real backend here) quiet.
function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
    // No backend in this test: the queries fail by design. Silence the expected
    // network errors so the routing assertions read cleanly.
    logger: { log: () => {}, warn: () => {}, error: () => {} },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('App navigation', () => {
  it('starts on the dashboard and navigates to the live market page', () => {
    renderApp();
    expect(screen.getByText('Trading Risk Dashboard')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Live Market' }));

    // The data-source banner is unique to the market page and renders before
    // any data loads.
    expect(screen.getByText(/Yahoo Finance/)).toBeInTheDocument();
    expect(screen.queryByText('Trading Risk Dashboard')).not.toBeInTheDocument();
  });
});
