import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import CloudUploadRoundedIcon from '@mui/icons-material/CloudUploadRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import DescriptionRoundedIcon from '@mui/icons-material/DescriptionRounded'
import SendRoundedIcon from '@mui/icons-material/SendRounded'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import { ChangeEvent, useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { DocumentType, SupplierDetail, SupplierDocument } from '../api/types'
import { StatusChip } from '../components/StatusChip'

const documentLabels: Record<DocumentType, string> = {
  registration: 'Supplier registration form',
  tax: 'Tax registration certificate',
  insurance: 'Insurance certificate',
}

export function SupplierPortalPage() {
  const { supplierId = '' } = useParams()
  const [supplier, setSupplier] = useState<SupplierDetail | null>(null)
  const [documentType, setDocumentType] = useState<DocumentType>('registration')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadSupplier = useCallback(async () => {
    try {
      setSupplier(await api.getSupplier(supplierId))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Supplier case could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [supplierId])

  useEffect(() => { void loadSupplier() }, [loadSupplier])

  if (loading) return <Box sx={{ display: 'grid', placeItems: 'center', py: 8 }}><CircularProgress /></Box>
  if (!supplier) return <Alert severity="error">{error || 'Supplier case was not found.'}</Alert>

  const editable = supplier.status === 'new' || supplier.status === 'changes_requested'
  const uploadedTypes = new Set(supplier.documents.map((document) => document.document_type))
  const availableTypes = (Object.entries(documentLabels) as [DocumentType, string][])
    .filter(([value]) => !uploadedTypes.has(value))
  const effectiveType = availableTypes.some(([value]) => value === documentType)
    ? documentType
    : availableTypes[0]?.[0]
  const requestedDocumentIds = new Set(supplier.change_request?.documents.map((item) => item.document_id) ?? [])
  const allReady = uploadedTypes.size === Object.keys(documentLabels).length
    && supplier.documents.every((document) => document.processing_status === 'ready')
  const replacementsComplete = [...requestedDocumentIds]
    .every((documentId) => !supplier.documents.some((document) => document.id === documentId))

  async function runAction(action: () => Promise<{ message: string }>) {
    setWorking(true)
    setError('')
    setNotice('')
    try {
      const result = await action()
      setNotice(result.message)
      setSelectedFile(null)
      await loadSupplier()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'The action could not be completed.')
    } finally {
      setWorking(false)
    }
  }

  async function uploadDocument() {
    if (!selectedFile || !effectiveType) return
    setWorking(true)
    setError('')
    setNotice('')
    try {
      await api.uploadDocument(supplierId, effectiveType, selectedFile)
      setNotice('Document uploaded successfully.')
      setSelectedFile(null)
      await loadSupplier()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Document upload failed.')
    } finally {
      setWorking(false)
    }
  }

  async function deleteDocument(document: SupplierDocument) {
    if (!window.confirm(`Replace ${document.filename}? The current file will be removed.`)) return
    setWorking(true)
    setError('')
    setNotice('')
    try {
      await api.deleteDocument(supplierId, document.id)
      setNotice('Document removed. Upload its replacement before resubmitting.')
      await loadSupplier()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Document could not be removed.')
    } finally {
      setWorking(false)
    }
  }

  const workflowEvents = supplier.audit_events.filter((event) => [
    'supplier.submitted',
    'supplier.review_started',
    'supplier.changes_requested',
    'supplier.resubmitted',
    'supplier.approved',
    'supplier.rejected',
  ].includes(event.action))

  return (
    <Stack spacing={3}>
      <Button component={Link} to="/supplier" startIcon={<ArrowBackRoundedIcon />} sx={{ alignSelf: 'flex-start' }}>Back to my cases</Button>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={2}>
        <Box>
          <Typography variant="h4">{supplier.name}</Typography>
          <Typography color="text.secondary">Supplier case · review round {supplier.review_round || 'not started'}</Typography>
        </Box>
        <StatusChip status={supplier.status} />
      </Stack>

      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
      {notice && <Alert severity="success" onClose={() => setNotice('')}>{notice}</Alert>}

      {supplier.status === 'changes_requested' && supplier.change_request && (
        <Alert severity="warning">
          <Typography fontWeight={750}>Reviewer requested document changes</Typography>
          {supplier.change_request.general_reason && <Typography sx={{ mt: 0.5 }}>{supplier.change_request.general_reason}</Typography>}
          <Stack spacing={1} sx={{ mt: 1.5 }}>
            {supplier.change_request.documents.map((item) => (
              <Box key={item.document_id}>
                <Typography fontWeight={700}>{documentLabels[item.document_type]}: {item.filename}</Typography>
                <Typography variant="body2">{item.reason}</Typography>
              </Box>
            ))}
          </Stack>
          <Typography variant="body2" sx={{ mt: 1.5 }}>Remove each flagged file, upload its replacement, then resubmit the case.</Typography>
        </Alert>
      )}

      {supplier.status === 'submitted' || supplier.status === 'resubmitted' ? (
        <Alert severity="info">Your case is waiting in the reviewer queue. Documents are locked until the reviewer responds.</Alert>
      ) : null}
      {supplier.status === 'under_review' || supplier.status === 'processing' || supplier.status === 'needs_review' ? (
        <Alert severity="info">Review is in progress. You will be notified here if document changes are needed.</Alert>
      ) : null}
      {supplier.status === 'approved' && <Alert severity="success">Approved. ERP supplier ID: {supplier.erp_supplier_id}</Alert>}
      {supplier.status === 'rejected' && <Alert severity="error">Final rejection: {supplier.decision_reason}</Alert>}

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 2fr) minmax(300px, 1fr)' }, gap: 3 }}>
        <Card><CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Typography variant="h6">Your documents</Typography>
          <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>One ready file is required in each category.</Typography>
          {supplier.documents.length === 0 ? <Alert severity="info">No documents uploaded yet.</Alert> : (
            <Stack divider={<Divider flexItem />}>
              {supplier.documents.map((document) => {
                const replacementRequested = requestedDocumentIds.has(document.id)
                const canDelete = editable && (supplier.status === 'new' || replacementRequested)
                return (
                  <Stack key={document.id} direction="row" justifyContent="space-between" alignItems="center" spacing={2} sx={{ py: 2 }}>
                    <Stack direction="row" spacing={1.5} alignItems="center" sx={{ minWidth: 0 }}>
                      <DescriptionRoundedIcon color={replacementRequested ? 'warning' : 'primary'} />
                      <Box sx={{ minWidth: 0 }}>
                        <Typography noWrap fontWeight={650}>{document.filename}</Typography>
                        <Typography variant="caption" color="text.secondary">{documentLabels[document.document_type]} · {document.page_count} page(s)</Typography>
                        {replacementRequested && <Typography variant="caption" color="warning.main" display="block">Replacement required</Typography>}
                      </Box>
                    </Stack>
                    <Stack direction="row" spacing={0.5} alignItems="center">
                      <StatusChip status={document.processing_status} />
                      {canDelete && (
                        <Tooltip title={replacementRequested ? 'Remove and replace' : 'Delete document'}>
                          <IconButton color="error" disabled={working} onClick={() => void deleteDocument(document)}><DeleteOutlineRoundedIcon /></IconButton>
                        </Tooltip>
                      )}
                    </Stack>
                  </Stack>
                )
              })}
            </Stack>
          )}
        </CardContent></Card>

        <Stack spacing={2}>
          <Card><CardContent sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Typography variant="h6">Upload document</Typography>
              {!editable ? <Alert severity="info">Uploads are locked while this case is with the reviewer.</Alert> : effectiveType ? (
                <>
                  <TextField select label="Document type" value={effectiveType} onChange={(event) => setDocumentType(event.target.value as DocumentType)}>
                    {availableTypes.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
                  </TextField>
                  <Button component="label" variant="outlined" startIcon={<CloudUploadRoundedIcon />} disabled={working}>
                    {selectedFile ? 'Change file' : 'Choose file'}
                    <input hidden type="file" accept="application/pdf,text/plain,.pdf,.txt" onChange={(event: ChangeEvent<HTMLInputElement>) => setSelectedFile(event.target.files?.[0] ?? null)} />
                  </Button>
                  {selectedFile && <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{selectedFile.name}</Typography>}
                  <Button variant="contained" disabled={!selectedFile || working} onClick={() => void uploadDocument()}>Upload document</Button>
                </>
              ) : <Alert severity="success">All required categories are uploaded.</Alert>}
            </Stack>
          </CardContent></Card>

          {editable && (
            <Card><CardContent sx={{ p: 3 }}>
              <Typography variant="h6">Send to reviewer</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ my: 1.5 }}>
                {supplier.status === 'new' ? 'Submit after all three documents are ready.' : 'Resubmit after every flagged document has been replaced.'}
              </Typography>
              <Button
                fullWidth
                variant="contained"
                startIcon={<SendRoundedIcon />}
                disabled={!allReady || !replacementsComplete || working}
                onClick={() => void runAction(() => supplier.status === 'new' ? api.submitSupplier(supplierId) : api.resubmitSupplier(supplierId))}
              >
                {supplier.status === 'new' ? 'Submit for review' : 'Resubmit changes'}
              </Button>
            </CardContent></Card>
          )}
        </Stack>
      </Box>

      <Card><CardContent sx={{ p: { xs: 3, md: 4 } }}>
        <Typography variant="h6">Case history</Typography>
        {workflowEvents.length === 0 ? <Typography color="text.secondary" sx={{ mt: 1 }}>The review history will appear after submission.</Typography> : (
          <Stack divider={<Divider flexItem />} sx={{ mt: 1 }}>
            {workflowEvents.map((event) => (
              <Box key={event.id} sx={{ py: 1.5 }}>
                <Typography fontWeight={650}>{event.action.replaceAll('.', ' ').replaceAll('_', ' ')}</Typography>
                <Typography variant="caption" color="text.secondary">{new Date(event.created_at).toLocaleString()}</Typography>
              </Box>
            ))}
          </Stack>
        )}
      </CardContent></Card>
    </Stack>
  )
}
