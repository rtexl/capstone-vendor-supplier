import { Chip } from '@mui/material'
import type { ProcessingStatus, SupplierStatus } from '../api/types'

interface StatusChipProps {
  status: SupplierStatus | ProcessingStatus
}

const labels: Record<StatusChipProps['status'], string> = {
  new: 'New',
  submitted: 'Submitted',
  under_review: 'Under review',
  processing: 'Processing',
  needs_review: 'Needs review',
  changes_requested: 'Changes requested',
  resubmitted: 'Resubmitted',
  approved: 'Approved',
  rejected: 'Rejected',
  ready: 'Ready',
  failed: 'Failed',
}

export function StatusChip({ status }: StatusChipProps) {
  const color = status === 'approved' || status === 'ready'
    ? 'success'
    : status === 'failed' || status === 'rejected'
      ? 'error'
      : status === 'needs_review' || status === 'changes_requested' || status === 'resubmitted'
        ? 'warning'
        : 'default'

  return <Chip label={labels[status]} color={color} size="small" />
}
