import { useMemo } from 'react';
import { Typography } from '@mui/material';
import Plotly from 'plotly.js-dist-min';
import type { PlotParams } from 'react-plotly.js';
import createPlotlyComponent from 'react-plotly.js/factory';

import type { MarketQuote } from '../../api/types';

const Plot = createPlotlyComponent(Plotly);

interface PriceChartProps {
  quote: MarketQuote;
}

// One chart for the selected commodity. Memoised so the 5-second poll only
// rebuilds the trace when the quote actually changes.
export function PriceChart({ quote }: PriceChartProps) {
  const data = useMemo<PlotParams['data']>(
    () => [
      {
        type: 'scatter',
        mode: 'lines',
        x: quote.series.map((p) => p.t),
        y: quote.series.map((p) => p.price),
        line: { color: '#1976d2' },
        hovertemplate: `%{x|%H:%M:%S} UTC: ${quote.currency} %{y:,.2f}<extra></extra>`,
      },
    ],
    [quote],
  );

  const layout: PlotParams['layout'] = {
    height: 320,
    margin: { l: 72, r: 16, t: 8, b: 40 },
    xaxis: { title: { text: 'Time (UTC)' } },
    yaxis: { title: { text: `Price (${quote.currency} / ${quote.unit})` } },
  };

  return (
    <>
      <Typography variant="caption" color="text.secondary">
        Synthetic price series · {quote.name} ({quote.symbol})
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
