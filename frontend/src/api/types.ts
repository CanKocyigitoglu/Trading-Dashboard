// TypeScript mirrors of the backend API response models. The backend's
// generated OpenAPI schema is the source of truth; these types track it.

export interface PositionOut {
  position_id: string;
  desk: string;
  trader: string;
  instrument: string;
  commodity: string;
  unit: string;
  currency: string;
  side: string;
  quantity: number;
  avg_price: number;
  market_price: number | null;
  market_value: number | null;
  unrealised_pl: number | null;
  var_1d: number | null;
  exposure_limit: number;
  utilisation_pct: number | null;
  as_of: string;
  data_quality: string;
}

export interface PositionsResponse {
  items: PositionOut[];
  total: number;
  limit: number;
  offset: number;
  currency: string | null;
  source_timestamp: string | null;
}

export interface SummaryOut {
  currency: string;
  net_exposure: number;
  gross_exposure: number;
  total_unrealised_pl: number;
  total_var_1d_illustrative: number;
  position_count: number;
  incomplete_position_count: number;
  source_timestamp: string;
  evaluation_timestamp: string;
}

export interface AlertOut {
  rule_id: string;
  severity: string;
  entity_type: string;
  desk: string | null;
  trader: string | null;
  instrument: string | null;
  observed: string;
  threshold: string;
  reason: string;
  detail_reference: string | null;
  evaluation_timestamp: string;
  status: string;
}

export interface AlertsResponse {
  items: AlertOut[];
  evaluation_timestamp: string;
}

export interface FilterOptions {
  desks: string[];
  traders: string[];
  commodities: string[];
}

export interface MarketSeriesPoint {
  t: string;
  price: number;
}

export interface MarketQuote {
  symbol: string;
  name: string;
  commodity: string;
  unit: string;
  currency: string;
  last_price: number;
  previous_price: number;
  change: number;
  change_pct: number | null;
  as_of: string;
  series: MarketSeriesPoint[];
}

export interface MarketOverviewResponse {
  as_of: string;
  synthetic: boolean;
  quotes: MarketQuote[];
}

export interface Filters {
  desks: string[];
  traders: string[];
  commodities: string[];
}
