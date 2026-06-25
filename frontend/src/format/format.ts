// Presentation formatting. The frontend owns currency, number, unit and
// timestamp formatting; the backend supplies raw values. `null` means the
// value is unavailable and is shown distinctly from zero.

export const MISSING = '—';

const LOCALE = 'en-GB';
const DISPLAY_TIMEZONE = 'Europe/London';

export function formatMoney(
  value: number | null | undefined,
  currency: string,
  fractionDigits = 0,
): string {
  if (value === null || value === undefined) return MISSING;
  return new Intl.NumberFormat(LOCALE, {
    style: 'currency',
    currency,
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value === null || value === undefined) return MISSING;
  return new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function formatPercent(value: number | null | undefined, fractionDigits = 1): string {
  if (value === null || value === undefined) return MISSING;
  return `${value.toFixed(fractionDigits)}%`;
}

// Render an ISO/UTC timestamp in the default display timezone (Europe/London).
export function formatDateTimeLondon(iso: string | null | undefined): string {
  if (!iso) return MISSING;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return MISSING;
  return new Intl.DateTimeFormat(LOCALE, {
    timeZone: DISPLAY_TIMEZONE,
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}
