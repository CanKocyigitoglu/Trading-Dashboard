import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';

import { ApiError } from '../../api/client';
import {
  useIngest,
  useIngestionRuns,
  useMarketHistory,
  useMarketOverview,
} from '../../api/hooks';
import { formatDateTimeLondon } from '../../format/format';
import { MarketQuotesTable } from './MarketQuotesTable';
import { PriceChart } from './PriceChart';

export function MarketPage() {
  const query = useMarketOverview();
  const data = query.data;
  const quotes = data?.quotes ?? [];

  const ingest = useIngest();
  const runsQuery = useIngestionRuns();
  const lastRun = runsQuery.data?.items[0];

  // null = "follow the first quote"; a symbol once the user picks one.
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const selectedQuote = quotes.find((q) => q.symbol === selectedSymbol) ?? quotes[0] ?? null;

  const historyQuery = useMarketHistory(selectedQuote?.symbol ?? null);
  const history = historyQuery.data;
  // Prefer persisted history; fall back to the overview's recent series so the
  // chart is never blank while history loads.
  const series = history && history.points.length > 0 ? history.points : selectedQuote?.series ?? [];

  const loadError = query.error as ApiError | null;
  const dbNotConfigured = loadError?.code === 'DB_NOT_CONFIGURED';
  const staleCount = quotes.filter((q) => q.stale).length;
  const staleMinutes = data ? Math.round(data.stale_after_seconds / 60) : 0;

  return (
    <Box sx={{ p: 3, maxWidth: 1500, mx: 'auto' }}>
      <Typography variant="h4">Live Market</Typography>
      <Typography variant="body2" color="text.secondary">
        Real commodity futures · TMT trading risk
      </Typography>
      <Alert severity="info" sx={{ mt: 1 }}>
        Free, unofficial source (Yahoo Finance) — <strong>not</strong> the firm&apos;s
        authoritative price feed. Quotes are stored as application-owned history for later
        analysis. Grains quote in US cents (USc) per bushel and copper in USD per lb — source units
        are preserved, not converted.
      </Alert>

      <Box sx={{ mt: 2, mb: 1, display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="body2">
          Data as of: <strong>{formatDateTimeLondon(data?.as_of)}</strong> (Europe/London)
        </Typography>
        {lastRun && (
          <Typography variant="body2" color="text.secondary">
            Last ingested: <strong>{formatDateTimeLondon(lastRun.finished_at)}</strong> ·{' '}
            {lastRun.status} · {lastRun.rows_written} new rows
          </Typography>
        )}
        <Button
          variant="outlined"
          size="small"
          onClick={() => ingest.mutate()}
          disabled={ingest.isLoading}
        >
          {ingest.isLoading ? 'Refreshing…' : 'Refresh now'}
        </Button>
        {query.isFetching && (
          <Stack direction="row" spacing={1} alignItems="center">
            <CircularProgress size={14} />
            <Typography variant="caption">Updating…</Typography>
          </Stack>
        )}
      </Box>

      {ingest.isError && (
        <Alert severity="error" sx={{ mt: 1 }}>
          Ingestion failed: {(ingest.error as ApiError).message}
        </Alert>
      )}
      {ingest.isSuccess && ingest.data && (
        <Alert severity="success" sx={{ mt: 1 }}>
          Ingestion {ingest.data.status}: {ingest.data.rows_written} new rows across{' '}
          {ingest.data.symbols_requested} commodities.
        </Alert>
      )}

      {staleCount > 0 && (
        <Alert severity="warning" sx={{ mt: 1 }} icon={<Chip size="small" label="Stale" />}>
          {staleCount} of {quotes.length} quotes are older than {staleMinutes} min — the market may
          be closed, or ingestion has stopped.
        </Alert>
      )}

      {loadError && data && !dbNotConfigured && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Background refresh failed ({loadError.message}). Showing last successful data.
        </Alert>
      )}

      <Box sx={{ mt: 2 }}>
        {query.isLoading && !data ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
            <CircularProgress />
          </Box>
        ) : dbNotConfigured ? (
          <Alert severity="error">
            The market database is not configured. Set <code>DATABASE_URL</code> in{' '}
            <code>backend/.env</code>, run <code>make migrate</code>, then ingest with{' '}
            <code>make ingest</code> (or the “Refresh now” button).
          </Alert>
        ) : loadError && !data ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => query.refetch()}>
                Retry
              </Button>
            }
          >
            Could not load market data: {loadError.message}
          </Alert>
        ) : quotes.length === 0 ? (
          <Alert severity="info">
            No market data yet. Click “Refresh now” (or run <code>make ingest</code>) to fetch and
            store the first snapshot.
          </Alert>
        ) : (
          <Stack spacing={3}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Market quotes
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last price and the move versus the previous stored point. Currency and unit are
                shown per commodity.
              </Typography>
              <Box sx={{ mt: 1 }}>
                <MarketQuotesTable quotes={quotes} />
              </Box>
            </Paper>

            {selectedQuote && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 2,
                    mb: 1,
                  }}
                >
                  <Typography variant="subtitle1">Price history (stored)</Typography>
                  <FormControl size="small" sx={{ minWidth: 220 }}>
                    <InputLabel id="commodity-label">Commodity</InputLabel>
                    <Select
                      labelId="commodity-label"
                      label="Commodity"
                      value={selectedQuote.symbol}
                      onChange={(e) => setSelectedSymbol(e.target.value)}
                    >
                      {quotes.map((q) => (
                        <MenuItem key={q.symbol} value={q.symbol}>
                          {q.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <PriceChart
                  series={series}
                  name={history?.name ?? selectedQuote.name}
                  symbol={selectedQuote.symbol}
                  currency={history?.currency ?? selectedQuote.currency}
                  unit={history?.unit ?? selectedQuote.unit}
                />
              </Paper>
            )}
          </Stack>
        )}
      </Box>
    </Box>
  );
}
