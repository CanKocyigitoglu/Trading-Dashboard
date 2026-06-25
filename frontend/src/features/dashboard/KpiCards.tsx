import { Box, Card, CardContent, Typography } from '@mui/material';

import type { SummaryOut } from '../../api/types';
import { formatMoney, formatNumber } from '../../format/format';

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
}

function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <Card variant="outlined" sx={{ minWidth: 180, flex: '1 1 180px' }}>
      <CardContent>
        <Typography variant="caption" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h6" sx={{ fontVariantNumeric: 'tabular-nums' }}>
          {value}
        </Typography>
        {hint && (
          <Typography variant="caption" color="text.secondary">
            {hint}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

interface KpiCardsProps {
  summary: SummaryOut;
  openExceptions: number;
}

export function KpiCards({ summary, openExceptions }: KpiCardsProps) {
  const ccy = summary.currency;
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
      <KpiCard label={`Net Exposure (${ccy})`} value={formatMoney(summary.net_exposure, ccy)} />
      <KpiCard label={`Gross Exposure (${ccy})`} value={formatMoney(summary.gross_exposure, ccy)} />
      <KpiCard
        label={`Unrealised P/L (${ccy})`}
        value={formatMoney(summary.total_unrealised_pl, ccy)}
      />
      <KpiCard
        label={`1-Day VaR (${ccy})`}
        value={formatMoney(summary.total_var_1d_illustrative, ccy)}
        hint="Illustrative simple sum; ignores diversification"
      />
      <KpiCard
        label="Open Exceptions"
        value={formatNumber(openExceptions)}
        hint={
          summary.incomplete_position_count > 0
            ? `${summary.incomplete_position_count} position(s) incomplete`
            : undefined
        }
      />
    </Box>
  );
}
