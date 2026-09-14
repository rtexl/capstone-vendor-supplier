import AddRoundedIcon from '@mui/icons-material/AddRounded'
import BusinessRoundedIcon from '@mui/icons-material/BusinessRounded'
import DescriptionRoundedIcon from '@mui/icons-material/DescriptionRounded'
import { Alert, Box, Button, Card, CardActionArea, CardContent, CircularProgress, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { SupplierSummary } from '../api/types'
import { StatusChip } from '../components/StatusChip'

interface DashboardPageProps {
  mode: 'supplier' | 'reviewer'
}

export function DashboardPage({ mode }: DashboardPageProps) {
  const [suppliers, setSuppliers] = useState<SupplierSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listSuppliers()
      .then(setSuppliers)
      .catch((requestError: Error) => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [])

  const visibleSuppliers = mode === 'reviewer'
    ? suppliers.filter((supplier) => supplier.status !== 'new')
    : suppliers

  return (
    <Stack spacing={4}>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={2}>
        <Box>
          <Typography variant="h4">{mode === 'reviewer' ? 'Review queue' : 'My supplier cases'}</Typography>
          <Typography color="text.secondary" sx={{ mt: 0.75 }}>
            {mode === 'reviewer'
              ? 'Review submitted cases, request corrections, and make final decisions.'
              : 'Upload required documents, submit them, and respond to reviewer feedback.'}
          </Typography>
        </Box>
        {mode === 'supplier' && <Button component={Link} to="/supplier/new" variant="contained" startIcon={<AddRoundedIcon />}>Create case</Button>}
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}
      {loading && <Box sx={{ display: 'grid', placeItems: 'center', py: 8 }}><CircularProgress /></Box>}
      {!loading && !error && visibleSuppliers.length === 0 && (
        <Card><CardContent sx={{ py: 7, textAlign: 'center' }}>
          <BusinessRoundedIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
          <Typography variant="h6">{mode === 'reviewer' ? 'No submitted cases' : 'No supplier cases yet'}</Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {mode === 'reviewer' ? 'Cases appear here after a supplier submits them.' : 'Create the first case to begin the intake workflow.'}
          </Typography>
          {mode === 'supplier' && <Button component={Link} to="/supplier/new" variant="contained">Create supplier</Button>}
        </CardContent></Card>
      )}

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
        {visibleSuppliers.map((supplier) => (
          <Card key={supplier.id}>
            <CardActionArea component={Link} to={`/${mode}/${supplier.id}`}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
                  <Box>
                    <Typography variant="h6">{supplier.name}</Typography>
                    <Typography color="text.secondary" variant="body2">{supplier.country || 'Country not provided'}</Typography>
                  </Box>
                  <StatusChip status={supplier.status} />
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 3, color: 'text.secondary' }}>
                  <DescriptionRoundedIcon fontSize="small" />
                  <Typography variant="body2">{supplier.document_count} document{supplier.document_count === 1 ? '' : 's'}</Typography>
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>
    </Stack>
  )
}
