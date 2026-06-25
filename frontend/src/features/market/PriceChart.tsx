import { useMemo } from 'react';
import { Typography } from '@mui/material';
import Plotly from 'plotly.js-dist-min';
import type { PlotParams } from 'react-plotly.js';
import createPlotlyComponent from 'react-plotly.js/factory';

import type { MarketSeriesPoint } from '../../api/types';

const Plot = createPlotlyComponent(Plotly);

interface PriceChartProps {
  series: MarketSeriesPoint[];
  name: string;
  symbol: string;
  currency: string;
  unit: string;
}

// One chart for the selected commodity. Memoised so the poll only rebuilds the
// trace when the series actually changes.
export function PriceChart({ series, name, symbol, currency, unit }: PriceChartProps) {
  const data = useMemo<PlotParams['data']>(
    () => [
      {
        type: 'scatter',
        mode: 'lines',
        x: series.map((p) => p.t),
        y: series.map((p) => p.price),
        line: { color: '#1976d2' },
        hovertemplate: `%{x|%d %b %H:%M} UTC: ${currency} %{y:,.2f}<extra></extra>`,
      },
    ],
    [series, currency],
  );

  const layout: PlotParams['layout'] = {
    height: 320,
    margin: { l: 72, r: 16, t: 8, b: 40 },
    xaxis: { title: { text: 'Time (UTC)' } },
    yaxis: { title: { text: `Price (${currency} / ${unit})` } },
  };

  return (
    <>
      <Typography variant="caption" color="text.secondary">
        Price series · {name} ({symbol})
      </Typography>
      <Plot
        data={data}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
        useResizeHandler
      />
    </>
  );
}
