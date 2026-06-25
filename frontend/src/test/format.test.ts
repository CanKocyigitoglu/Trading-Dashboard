import { describe, expect, it } from 'vitest';

import {
  MISSING,
  formatDateTimeLondon,
  formatMoney,
  formatNumber,
  formatPercent,
} from '../format/format';

describe('formatMoney', () => {
  it('shows the missing placeholder for null, not zero', () => {
    expect(formatMoney(null, 'USD')).toBe(MISSING);
  });

  it('formats zero distinctly from missing', () => {
    expect(formatMoney(0, 'USD')).not.toBe(MISSING);
  });

  it('formats whole amounts with thousands separators', () => {
    expect(formatMoney(26880500, 'USD')).toContain('26,880,500');
  });
});

describe('formatPercent and formatNumber', () => {
  it('formats a percentage to one decimal', () => {
    expect(formatPercent(85)).toBe('85.0%');
  });

  it('returns missing placeholder for null percent', () => {
    expect(formatPercent(null)).toBe(MISSING);
  });

  it('formats numbers with separators', () => {
    expect(formatNumber(50000)).toBe('50,000');
  });
});

describe('formatDateTimeLondon', () => {
  it('renders a UTC instant in Europe/London (BST in June = UTC+1)', () => {
    // 15:30 UTC on 2026-06-24 is 16:30 in London during British Summer Time.
    expect(formatDateTimeLondon('2026-06-24T15:30:00Z')).toContain('16:30');
  });

  it('returns missing placeholder for null', () => {
    expect(formatDateTimeLondon(null)).toBe(MISSING);
  });
});
