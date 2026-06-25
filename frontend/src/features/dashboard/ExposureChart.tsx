import { Typography } from '@mui/material';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import type { PlotParams } from 'react-plotly.js';

import type { PositionOut } from '../../api/types';

const Plot = createPlotlyComponent(Plotly);

interface ExposureChartProps {
  positions: PositionOut[];
  currency: string;
}

// Concentration view: gross exposure (absolute market value) by desk. The
// per-position market values come from the backend; grouping them for the
// chart is a presentation concern, not a financial definition.
export function ExposureChart({ positions, currency }: ExposureChartProps) {
  const grossByDesk = new Map<string, number>();
  for (const p of positions) {
    if (p.market_value !== null) {
      grossByDesk.set(p.desk, (grossByDesk.get(p.desk) ?? 0) + Math.abs(p.market_value));
    }
  }

  const entries = [...grossByDesk.entries()].sort((a, b) => a[1] - b[1]);
  const desks = entries.map(([desk]) => desk);
  const values = entries.map(([, value]) => value);

  const data: PlotParams['data'] = [
    {
      type: 'bar',
      orientation: 'h',
      x: values,
      y: desks,
      marker: { color: '#1976d2' },
      hovertemplate: `%{y}: ${currency} %{x:,.0f}<extra></extra>`,
    },
  ];

  const layout: PlotParams['layout'] = {
    height: 320,
    margin: { l: 110, r: 16, t: 8, b: 40 },
    xaxis: { title: { text: `Gross Exposure (${currency})` } },
    yaxis: { automargin: true },
  };

  return (
    <>
      <Typography variant="subtitle1" gutterBottom>
        Exposure concentration by desk
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
