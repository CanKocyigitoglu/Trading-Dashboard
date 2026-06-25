import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { AlertOut } from '../../api/types';
import { AlertsPanel } from './AlertsPanel';

const breach: AlertOut = {
  rule_id: 'EXPOSURE_UTILISATION_BREACH',
  severity: 'high',
  entity_type: 'position',
  desk: 'Power',
  trader: 'Carol Diaz',
  instrument: 'German Power Baseload',
  observed: '108.5%',
  threshold: '>= 100.0%',
  reason: 'Gross exposure is at or above the position exposure limit.',
  detail_reference: 'P005',
  evaluation_timestamp: '2026-06-24T16:00:00Z',
  status: 'open',
};

describe('AlertsPanel', () => {
  it('shows severity as text and renders the alert details', () => {
    render(<AlertsPanel alerts={[breach]} />);
    // Severity is conveyed as text (not colour alone).
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText(/German Power Baseload/)).toBeInTheDocument();
    expect(screen.getByText('108.5%')).toBeInTheDocument();
    expect(screen.getByText(/at or above the position exposure limit/)).toBeInTheDocument();
  });

  it('renders an empty-state message when there are no alerts', () => {
    render(<AlertsPanel alerts={[]} />);
    expect(screen.getByText('No alerts for the current selection.')).toBeInTheDocument();
  });
});
