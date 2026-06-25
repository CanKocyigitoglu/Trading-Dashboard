import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
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
import { useMarketOverview } from '../../api/hooks';
import { formatDateTimeLondon } from '../../format/format';
import { MarketQuotesTable } from './MarketQuotesTable';
import { PriceChart } from './PriceChart';

export function MarketPage() {
  const query = useMarketOverview();
  const data = query.data;
  const quotes = data?.quotes ?? [];

  // null = "follow the first quote"; a symbol once the user picks one.
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const selectedQuote = quotes.find((q) => q.symbol === selectedSymbol) ?? quotes[0] ?? null;

  const loadError = query.error as ApiError | null;

  return (
    <Box sx={{ p: 3, maxWidth: 1500, mx: 'auto' }}>
      <Typography variant="h4">Live Market</Typography>
      <Typography variant="body2" color="text.secondary">
        Synthetic commodity prices · TMT trading risk
      </Typography>
      <Alert severity="info" sx={{ mt: 1 }}>
        Illustrative synthetic market data — not a live feed or real prices.
      </Alert>

      <Box
        sx={{ mt: 2, mb: 1, display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}
      >
        <Typography variant="body2">
          Data as of: <strong>{formatDateTimeLondon(data?.as_of)}</strong> (Europe/London)
        </Typography>
        {query.isFetching && (
          <Stack direction="row" spacing={1} alignItems="center">
            <CircularProgress size={14} />
            <Typography variant="caption">Updating…</Typography>
          </Stack>
        )}
      </Box>

      {loadError && data && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Background refresh failed ({loadError.message}). Showing last successful data.
        </Alert>
      )}

      <Box sx={{ mt: 2 }}>
        {query.isLoading && !data ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
            <CircularProgress />
          </Box>
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
          <Alert severity="info">No market data available.</Alert>
        ) : (
          <Stack spacing={3}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Market quotes
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last price and the move versus the previous synthetic tick. Currency and unit are
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
                  <Typography variant="subtitle1">Price history</Typography>
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
                <PriceChart quote={selectedQuote} />
              </Paper>
            )}
          </Stack>
        )}
      </Box>
    </Box>
  );
}
