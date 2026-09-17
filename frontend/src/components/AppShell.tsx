import AddBusinessRoundedIcon from '@mui/icons-material/AddBusinessRounded'
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded'
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded'
import RateReviewRoundedIcon from '@mui/icons-material/RateReviewRounded'
import StorefrontRoundedIcon from '@mui/icons-material/StorefrontRounded'
import { AppBar, Box, Button, Chip, Container, Stack, Toolbar, Typography } from '@mui/material'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { SupplierAssistantPopover } from './SupplierAssistantPopover'

export function AppShell() {
  const location = useLocation()
  const reviewerPortal = location.pathname.startsWith('/reviewer')
  const portalRoot = reviewerPortal ? '/reviewer' : '/supplier'

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ minHeight: 68, gap: 2 }}>
            <Box sx={{ display: 'grid', placeItems: 'center', width: 38, height: 38, borderRadius: 2, bgcolor: 'tertiary.main', color: 'white' }}>
              <AutoAwesomeRoundedIcon fontSize="small" />
            </Box>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6">VendorLens</Typography>
              <Chip
                size="small"
                variant="outlined"
                color={reviewerPortal ? 'secondary' : 'primary'}
                icon={reviewerPortal ? <RateReviewRoundedIcon /> : <StorefrontRoundedIcon />}
                label={reviewerPortal ? 'Reviewer workspace' : 'Supplier portal'}
              />
            </Box>
            <Stack direction="row" spacing={1}>
              <Button component={Link} to={portalRoot} startIcon={<DashboardRoundedIcon />} variant={location.pathname === portalRoot ? 'contained' : 'text'}>
                {reviewerPortal ? 'Review queue' : 'My cases'}
              </Button>
              {!reviewerPortal && (
                <Button component={Link} to="/supplier/new" startIcon={<AddBusinessRoundedIcon />} variant={location.pathname === '/supplier/new' ? 'contained' : 'outlined'}>
                  New case
                </Button>
              )}
              <Button component={Link} to={reviewerPortal ? '/supplier' : '/reviewer'} variant="text">
                {reviewerPortal ? 'Supplier portal' : 'Reviewer workspace'}
              </Button>
            </Stack>
          </Toolbar>
        </Container>
      </AppBar>
      <Container maxWidth="lg" component="main" sx={{ py: { xs: 3, md: 5 } }}>
        <Outlet />
      </Container>
      <SupplierAssistantPopover />
    </Box>
  )
}
