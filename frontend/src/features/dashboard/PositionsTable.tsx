import {
  DataGrid,
  type GridColDef,
  type GridValueFormatterParams,
} from '@mui/x-data-grid';

import type { PositionOut } from '../../api/types';
import { formatMoney, formatNumber, formatPercent } from '../../format/format';

interface PositionsTableProps {
  positions: PositionOut[];
  currency: string;
  loading: boolean;
}

function buildColumns(currency: string): GridColDef<PositionOut>[] {
  const money =
    (digits: number) =>
    (params: GridValueFormatterParams<number | null>): string =>
      formatMoney(params.value, currency, digits);

  return [
    { field: 'desk', headerName: 'Desk', width: 130 },
    { field: 'trader', headerName: 'Trader', width: 130 },
    { field: 'instrument', headerName: 'Instrument', flex: 1, minWidth: 180 },
    { field: 'commodity', headerName: 'Commodity', width: 120 },
    { field: 'side', headerName: 'Side', width: 80 },
    {
      field: 'quantity',
      headerName: 'Quantity',
      type: 'number',
      width: 120,
      valueFormatter: (p: GridValueFormatterParams<number>) => formatNumber(p.value),
    },
    { field: 'unit', headerName: 'Unit', width: 80 },
    {
      field: 'avg_price',
      headerName: 'Avg Price',
      type: 'number',
      width: 110,
      valueFormatter: money(2),
    },
    {
      field: 'market_price',
      headerName: 'Market Price',
      type: 'number',
      width: 120,
      valueFormatter: money(2),
    },
    {
      field: 'market_value',
      headerName: 'Market Value',
      type: 'number',
      width: 140,
      valueFormatter: money(0),
    },
    {
      field: 'unrealised_pl',
      headerName: 'Unrealised P/L',
      type: 'number',
      width: 140,
      valueFormatter: money(0),
    },
    {
      field: 'var_1d',
      headerName: '1-Day VaR',
      type: 'number',
      width: 120,
      valueFormatter: money(0),
    },
    {
      field: 'utilisation_pct',
      headerName: 'Utilisation %',
      type: 'number',
      width: 120,
      valueFormatter: (p: GridValueFormatterParams<number | null>) => formatPercent(p.value),
    },
    {
      field: 'exposure_limit',
      headerName: 'Exposure Limit',
      type: 'number',
      width: 140,
      valueFormatter: money(0),
    },
    { field: 'data_quality', headerName: 'Data Quality', width: 120 },
  ];
}

export function PositionsTable({ positions, currency, loading }: PositionsTableProps) {
  return (
    <DataGrid
      rows={positions}
      columns={buildColumns(currency)}
      getRowId={(row) => row.position_id}
      loading={loading}
      autoHeight
      density="compact"
      disableRowSelectionOnClick
      initialState={{ pagination: { paginationModel: { pageSize: 10, page: 0 } } }}
      pageSizeOptions={[10, 25, 50]}
    />
  );
}
