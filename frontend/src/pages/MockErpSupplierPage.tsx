import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import BusinessRoundedIcon from '@mui/icons-material/BusinessRounded'
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded'
import DescriptionRoundedIcon from '@mui/icons-material/DescriptionRounded'
import LinkRoundedIcon from '@mui/icons-material/LinkRounded'
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Divider, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { SupplierDetail } from '../api/types'

const erpFieldLabels: Record<string, string> = {
  supplier_name: 'Legal name',
  tax_identifier: 'Tax identifier',
  address: 'Registered address',
  contact_name: 'Primary contact',
  contact_email: 'Contact email',
  contact_phone: 'Contact phone',
  payment_terms: 'Payment terms',
}

export function MockErpSupplierPage() {
  const { supplierId = '' } = useParams()
  const [supplier, setSupplier] = useState<SupplierDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getSupplier(supplierId)
      .then(setSupplier)
      .catch((requestError: Error) => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [supplierId])

  if (loading) return <Box sx={{ display: 'grid', placeItems: 'center', py: 10 }}><CircularProgress /></Box>
  if (!supplier) return <Alert severity="error">{error || 'The ERP record could not be loaded.'}</Alert>

  const visibleFields = supplier.extracted_fields.filter((field) => erpFieldLabels[field.field_name])

  return (
    <Stack spacing={3}>
      <Button
        component={Link}
        to={`/reviewer/${supplier.id}`}
        startIcon={<ArrowBackRoundedIcon />}
        sx={{ alignSelf: 'flex-start' }}
      >
        Back to VendorLens review
      </Button>

      <Card sx={{ overflow: 'hidden' }}>
        <Box sx={{ px: { xs: 3, md: 4 }, py: 3, bgcolor: '#0F172A', color: 'white' }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2}>
            <Stack direction="row" spacing={2} alignItems="center">
              <Box sx={{ display: 'grid', placeItems: 'center', width: 48, height: 48, borderRadius: 2, bgcolor: 'primary.main' }}>
                <BusinessRoundedIcon />
              </Box>
              <Box>
                <Typography variant="overline" sx={{ color: '#94A3B8' }}>Mock ERP vendor master</Typography>
                <Typography variant="h5">{supplier.name}</Typography>
              </Box>
            </Stack>
            <Chip
              icon={<CheckCircleRoundedIcon />}
              label="Active vendor"
              color="success"
              sx={{ alignSelf: { xs: 'flex-start', sm: 'center' } }}
            />
          </Stack>
        </Box>

        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          {supplier.status !== 'approved' ? (
            <Alert severity="warning">This supplier has not been approved, so no ERP vendor record is available.</Alert>
          ) : (
            <Stack spacing={4}>
              <Alert severity="info" icon={<LinkRoundedIcon />}>
                Prototype view: this page represents the downstream ERP record linked after reviewer approval.
              </Alert>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 3 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">ERP supplier ID</Typography>
                  <Typography fontWeight={750}>{supplier.erp_supplier_id}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Source system</Typography>
                  <Typography fontWeight={750}>VendorLens</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Created in ERP</Typography>
                  <Typography fontWeight={750}>
                    {supplier.decided_at ? new Date(supplier.decided_at).toLocaleString() : 'Just now'}
                  </Typography>
                </Box>
              </Box>

              <Divider />

              <Box>
                <Typography variant="h6" sx={{ mb: 2 }}>Vendor profile</Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                  {visibleFields.map((field) => (
                    <Box key={field.id} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
                      <Typography variant="caption" color="text.secondary">{erpFieldLabels[field.field_name]}</Typography>
                      <Typography sx={{ mt: 0.5 }}>{field.value}</Typography>
                    </Box>
                  ))}
                </Box>
              </Box>

              <Divider />

              <Stack direction="row" spacing={1.5} alignItems="center">
                <DescriptionRoundedIcon color="primary" />
                <Box>
                  <Typography fontWeight={700}>Supporting document references</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {supplier.documents.length} approved document{supplier.documents.length === 1 ? '' : 's'} linked from VendorLens
                  </Typography>
                </Box>
              </Stack>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Stack>
  )
}
