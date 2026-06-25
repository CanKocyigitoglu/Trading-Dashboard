import {
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

import type { AlertOut } from '../../api/types';

function severityColor(severity: string): 'error' | 'warning' | 'default' {
  if (severity === 'high') return 'error';
  if (severity === 'medium') return 'warning';
  return 'default';
}

function entityLabel(alert: AlertOut): string {
  if (alert.entity_type === 'dataset') return 'Dataset (all positions)';
  return [alert.desk, alert.trader, alert.instrument].filter(Boolean).join(' / ');
}

interface AlertsPanelProps {
  alerts: AlertOut[];
}

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  if (alerts.length === 0) {
    return (
      <Typography color="text.secondary">No alerts for the current selection.</Typography>
    );
  }

  return (
    <Table size="small" aria-label="alerts">
      <TableHead>
        <TableRow>
          <TableCell>Severity</TableCell>
          <TableCell>Entity</TableCell>
          <TableCell>Observed</TableCell>
          <TableCell>Threshold</TableCell>
          <TableCell>Reason</TableCell>
          <TableCell>Status</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {alerts.map((alert, index) => (
          <TableRow key={`${alert.rule_id}-${alert.detail_reference ?? index}`}>
            <TableCell>
              {/* Severity is shown as text as well as colour, never colour alone. */}
              <Chip
                label={alert.severity.toUpperCase()}
                color={severityColor(alert.severity)}
                size="small"
              />
            </TableCell>
            <TableCell>{entityLabel(alert)}</TableCell>
            <TableCell>{alert.observed}</TableCell>
            <TableCell>{alert.threshold}</TableCell>
            <TableCell>{alert.reason}</TableCell>
            <TableCell>{alert.status}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
