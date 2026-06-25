// Thin fetch client. Kept separate from presentation components: components
// call the query hooks, never fetch directly.

import type { Filters } from './types';

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api/v1';

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

function filtersToParams(filters?: Filters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters) {
    filters.desks.forEach((d) => params.append('desk', d));
    filters.traders.forEach((t) => params.append('trader', t));
    filters.commodities.forEach((c) => params.append('commodity', c));
  }
  return params;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { headers: { Accept: 'application/json' }, ...init });
  } catch (cause) {
    throw new ApiError(0, 'network_error', 'Could not reach the backend service.');
  }

  if (!response.ok) {
    let code = 'http_error';
    let message = `Request failed with status ${response.status}.`;
    try {
      const body = await response.json();
      // FastAPI nests our {code, message} under "detail" for HTTPException.
      const payload = body && typeof body === 'object' && 'detail' in body ? body.detail : body;
      if (payload && typeof payload === 'object') {
        code = payload.code ?? code;
        message = payload.message ?? message;
      }
    } catch {
      // response had no JSON body; keep the generic message
    }
    throw new ApiError(response.status, code, message);
  }

  return (await response.json()) as T;
}

export async function getJson<T>(path: string, filters?: Filters): Promise<T> {
  const params = filtersToParams(filters);
  const query = params.toString();
  return request<T>(`${API_BASE}${path}${query ? `?${query}` : ''}`);
}

export async function postJson<T>(path: string): Promise<T> {
  return request<T>(`${API_BASE}${path}`, { method: 'POST' });
}
