import { Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';

import type { MarketQuote } from '../../api/types';
import { MISSING, formatNumber } from '../../format/format';

// Signed display so the direction of a move reads from the text alone (the
// quotes table is a bounded ~10-row snapshot, so a plain table is enough — no
// sorting/pagination/virtualisation needed).
function formatSignedNumber(value: number | null | undefined, digits: number): string {
  if (value === null || value === undefined) return MISSING;
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, digits)}`;
}

function formatSignedPercent(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return MISSING;
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

interface MarketQuotesTableProps {
  quotes: MarketQuote[];
}

export function MarketQuotesTable({ quotes }: MarketQuotesTableProps) {
  return (
    <Table size="small" aria-label="market quotes">
      <TableHead>
        <TableRow>
          <TableCell>Symbol</TableCell>
          <TableCell>Commodity</TableCell>
          <TableCell align="right">Last</TableCell>
          <TableCell align="right">Change</TableCell>
          <TableCell align="right">Change %</TableCell>
          <TableCell>Unit</TableCell>
          <TableCell>Currency</TableCell>
          <TableCell>Status</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {quotes.map((q) => (
          <TableRow key={q.symbol}>
            <TableCell>{q.symbol}</TableCell>
            <TableCell>{q.commodity}</TableCell>
            <TableCell align="right">{formatNumber(q.last_price, 2)}</TableCell>
            <TableCell align="right">{formatSignedNumber(q.change, 2)}</TableCell>
            <TableCell align="right">{formatSignedPercent(q.change_pct)}</TableCell>
            <TableCell>{q.unit}</TableCell>
            <TableCell>{q.currency}</TableCell>
            <TableCell>{q.stale ? 'Stale' : 'Live'}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
