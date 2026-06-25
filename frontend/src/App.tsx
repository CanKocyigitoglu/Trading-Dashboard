import { Route, Routes } from 'react-router-dom';

import { AppLayout } from './app/AppLayout';
import { Dashboard } from './features/dashboard/Dashboard';
import { MarketPage } from './features/market/MarketPage';

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="market" element={<MarketPage />} />
      </Route>
    </Routes>
  );
}
