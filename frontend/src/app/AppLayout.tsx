import { AppBar, Box, Tab, Tabs, Toolbar, Typography } from '@mui/material';
import { Link as RouterLink, Outlet, useLocation } from 'react-router-dom';

// Application-wide navigation shell. Pages render into the <Outlet/> below, so
// the nav stays mounted while the active page swaps (and remounts) on route
// change.
const NAV = [
  { label: 'Dashboard', to: '/' },
  { label: 'Live Market', to: '/market' },
];

export function AppLayout() {
  const { pathname } = useLocation();
  const current = NAV.some((n) => n.to === pathname) ? pathname : false;

  return (
    <Box>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar variant="dense" sx={{ gap: 3 }}>
          <Typography variant="h6" sx={{ fontSize: 16, fontWeight: 600 }}>
            Trading Risk
          </Typography>
          <Tabs value={current} textColor="primary" indicatorColor="primary">
            {NAV.map((n) => (
              <Tab key={n.to} label={n.label} value={n.to} component={RouterLink} to={n.to} />
            ))}
          </Tabs>
        </Toolbar>
      </AppBar>
      <Outlet />
    </Box>
  );
}
