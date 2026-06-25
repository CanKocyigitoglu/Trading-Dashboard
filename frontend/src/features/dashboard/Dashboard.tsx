import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';

import { ApiError } from '../../api/client';
import { useAlerts, usePositions, useSummary } from '../../api/hooks';
import { formatDateTimeLondon } from '../../format/format';
import { AlertsPanel } from './AlertsPanel';
import { ExposureChart } from './ExposureChart';
import { FiltersBar } from './FiltersBar';
import { KpiCards } from './KpiCards';
import { PositionsTable } from './PositionsTable';
import { useUrlFilters } from './useUrlFilters';

export function Dashboard() {
  const [filters, setFilters] = useUrlFilters();
  const summaryQuery = useSummary(filters);
  const positionsQuery = usePositions(filters);
  const alertsQuery = useAlerts(filters);

  const positions = positionsQuery.data?.items ?? [];
  const isEmpty = positionsQuery.data?.total === 0;
  const currency =
    summaryQuery.data?.currency ?? positionsQuery.data?.currency ?? 'USD';
  const sourceTimestamp =
    summaryQuery.data?.source_timestamp ?? positionsQuery.data?.source_timestamp ?? null;

  const refreshing =
    summaryQuery.isFetching || positionsQuery.isFetching || alertsQuery.isFetching;
  const loadError = positionsQuery.error as ApiError | null;

  return (
    <Box sx={{ p: 3, maxWidth: 1500, mx: 'auto' }}>
      <Typography variant="h4">Trading Risk Dashboard</Typography>
      <Typography variant="body2" color="text.secondary">
        Internal decision-support prototype · TMT trading risk
      </Typography>
      <Alert severity="info" sx={{ mt: 1 }}>
        Synthetic demonstration data — not real positions.
      </Alert>

      <Box
        sx={{ mt: 2, mb: 1, display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}
      >
        <Typography variant="body2">
          Data as of: <strong>{formatDateTimeLondon(sourceTimestamp)}</strong> (Europe/London)
        </Typography>
        <Typography variant="body2">
          Reporting currency: <strong>{currency}</strong>
        </Typography>
        {refreshing && (
          <Stack direction="row" spacing={1} alignItems="center">
            <CircularProgress size={14} />
            <Typography variant="caption">Refreshing…</Typography>
          </Stack>
        )}
      </Box>

      <FiltersBar filters={filters} onChange={setFilters} />

      {loadError && positionsQuery.data && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Background refresh failed ({loadError.message}). Showing last successful data.
        </Alert>
      )}

      <Box sx={{ mt: 2 }}>
        {positionsQuery.isLoading && !positionsQuery.data ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
            <CircularProgress />
          </Box>
        ) : loadError && !positionsQuery.data ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={() => positionsQuery.refetch()}>
                Retry
              </Button>
            }
          >
            Could not load data: {loadError.message}
          </Alert>
        ) : isEmpty ? (
          <Alert severity="info">
            No positions match the selected filters. Adjust the filters to see data.
          </Alert>
        ) : (
          <Stack spacing={3}>
            {summaryQuery.data && (
              <KpiCards
                summary={summaryQuery.data}
                openExceptions={alertsQuery.data?.items.length ?? 0}
              />
            )}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <ExposureChart positions={positions} currency={currency} />
            </Paper>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Positions
              </Typography>
              <PositionsTable
                positions={positions}
                currency={currency}
                loading={positionsQuery.isFetching}
              />
            </Paper>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Alerts &amp; exceptions
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Severity is shown as text and colour. Each alert lists the affected entity, the
                observed value, the threshold and the reason it triggered.
              </Typography>
              <Box sx={{ mt: 1 }}>
                <AlertsPanel alerts={alertsQuery.data?.items ?? []} />
              </Box>
            </Paper>
          </Stack>
        )}
      </Box>
    </Box>
  );
}
