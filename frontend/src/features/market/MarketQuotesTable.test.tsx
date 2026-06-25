import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { MarketQuote } from '../../api/types';
import { MarketQuotesTable } from './MarketQuotesTable';

function quote(overrides: Partial<MarketQuote> = {}): MarketQuote {
  return {
    symbol: 'WTI',
    name: 'WTI Crude Futures',
    commodity: 'WTI Crude',
    unit: 'bbl',
    currency: 'USD',
    last_price: 78.5,
    previous_price: 78.0,
    change: 0.5,
    change_pct: 0.641,
    as_of: '2026-06-25T12:00:00Z',
    source_ts: '2026-06-25T12:00:00Z',
    ingested_at: '2026-06-25T12:00:05Z',
    stale: false,
    series: [
      { t: '2026-06-25T11:59:55Z', price: 78.0 },
      { t: '2026-06-25T12:00:00Z', price: 78.5 },
    ],
    ...overrides,
  };
}

describe('MarketQuotesTable', () => {
  it('shows a signed positive change and unit/currency', () => {
    render(<MarketQuotesTable quotes={[quote()]} />);
    expect(screen.getByText('WTI Crude')).toBeInTheDocument();
    expect(screen.getByText('+0.50')).toBeInTheDocument();
    expect(screen.getByText('+0.64%')).toBeInTheDocument();
    expect(screen.getByText('bbl')).toBeInTheDocument();
  });

  it('shows a negative change with a minus sign', () => {
    render(
      <MarketQuotesTable quotes={[quote({ change: -1.25, change_pct: -1.6 })]} />,
    );
    expect(screen.getByText('-1.25')).toBeInTheDocument();
    expect(screen.getByText('-1.60%')).toBeInTheDocument();
  });

  it('renders a dash when the percentage change is unavailable', () => {
    render(<MarketQuotesTable quotes={[quote({ change_pct: null })]} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('shows a text status for stale and live quotes', () => {
    render(<MarketQuotesTable quotes={[quote({ stale: true })]} />);
    expect(screen.getByText('Stale')).toBeInTheDocument();
  });
});
