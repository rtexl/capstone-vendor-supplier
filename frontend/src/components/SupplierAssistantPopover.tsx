import SupportAgentRoundedIcon from '@mui/icons-material/SupportAgentRounded'
import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded'
import { Box, Button, CircularProgress, Fab, Popover, Stack, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Link, useLocation } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import { api } from '../api/client'
import type { GeneralAssistantArea, GeneralAssistantMessage, GeneralAssistantResponse } from '../api/types'

const welcomeMessage: GeneralAssistantMessage = {
  role: 'assistant',
  content: 'Hi! I can explain VendorLens features and workflows, or take you directly to an area of the app. I cannot access supplier-specific data.',
}

export function SupplierAssistantPopover() {
  const location = useLocation()
  const [messages, setMessages] = useState<GeneralAssistantMessage[]>([welcomeMessage])
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [run, setRun] = useState<GeneralAssistantResponse['run'] | null>(null)
  const [links, setLinks] = useState<GeneralAssistantResponse['links']>([])
  const [error, setError] = useState('')
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)

  function currentArea(): GeneralAssistantArea {
    if (location.pathname === '/supplier/new') return 'create_supplier_case'
    if (location.pathname === '/supplier') return 'supplier_portal'
    if (location.pathname.startsWith('/supplier/')) return 'supplier_case'
    if (location.pathname === '/reviewer') return 'review_queue'
    return 'reviewer_case'
  }

  async function handleSubmit() {
    const trimmedQuestion = question.trim()
    if (trimmedQuestion.length < 3) return
    const nextMessages: GeneralAssistantMessage[] = [
      ...messages,
      { role: 'user', content: trimmedQuestion },
    ]
    setMessages(nextMessages)
    setQuestion('')
    setAsking(true)
    setError('')
    setLinks([])
    try {
      const result = await api.askGeneralAssistant(nextMessages, currentArea())
      setMessages((current) => [...current, { role: 'assistant', content: result.answer }])
      setRun(result.run)
      setLinks(result.links)
    } catch (requestError) {
      setQuestion(trimmedQuestion)
      setError(requestError instanceof Error ? requestError.message : 'The supplier assistant could not answer.')
    } finally {
      setAsking(false)
    }
  }

  function resetChat() {
    setMessages([welcomeMessage])
    setQuestion('')
    setRun(null)
    setLinks([])
    setError('')
  }

  return (
    <>
      <Fab
        color="primary"
        aria-label="Open supplier onboarding assistant"
        onClick={(event) => setAnchorEl(event.currentTarget)}
        sx={{
          position: 'fixed',
          right: { xs: 16, sm: 24 },
          bottom: { xs: 16, sm: 24 },
          zIndex: (theme) => theme.zIndex.fab,
        }}
      >
        <SupportAgentRoundedIcon />
      </Fab>
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        slotProps={{
          paper: {
            sx: {
              width: { xs: 'calc(100vw - 32px)', sm: 420 },
              maxWidth: 'calc(100vw - 32px)',
              overflow: 'hidden',
            },
          },
        }}
      >
        <Box sx={{ p: 2.5 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
            <Stack direction="row" spacing={1} alignItems="center">
              <SupportAgentRoundedIcon color="primary" />
              <Typography variant="h6">Onboarding assistant</Typography>
            </Stack>
            <Button size="small" onClick={resetChat} disabled={asking}>New chat</Button>
          </Stack>
          <Typography color="text.secondary" variant="caption" display="block" sx={{ mt: 0.75, mb: 1.75 }}>
            Application guidance and navigation only. Supplier records are never shared.
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25, maxHeight: 'min(360px, 48vh)', overflowY: 'auto', p: 1.5, bgcolor: 'action.hover', borderRadius: 2 }}>
            {messages.map((message, index) => (
              <Box
                key={`${message.role}-${index}`}
                sx={{
                  alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '92%',
                  px: 1.5,
                  py: 1.1,
                  borderRadius: 2,
                  bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  boxShadow: 1,
                }}
              >
                {message.role === 'assistant' ? (
                  <Box
                    sx={{
                      fontSize: '0.875rem',
                      lineHeight: 1.55,
                      overflowWrap: 'anywhere',
                      '& p': { m: 0 },
                      '& p + p': { mt: 1 },
                      '& h1, & h2, & h3': { fontSize: '0.95rem', lineHeight: 1.35, fontWeight: 750, m: 0, mb: 0.75 },
                      '& h1:not(:first-of-type), & h2:not(:first-of-type), & h3:not(:first-of-type)': { mt: 1.25 },
                      '& ul, & ol': { my: 0.75, pl: 2.5 },
                      '& li': { pl: 0.25 },
                      '& li + li': { mt: 0.4 },
                      '& strong': { fontWeight: 750 },
                      '& code': { px: 0.5, py: 0.15, borderRadius: 0.75, bgcolor: 'action.selected', fontFamily: 'monospace', fontSize: '0.8rem' },
                      '& pre': { m: 0, mt: 1, p: 1, overflowX: 'auto', borderRadius: 1, bgcolor: 'action.selected' },
                      '& pre code': { p: 0, bgcolor: 'transparent' },
                      '& hr': { my: 1, border: 0, borderTop: 1, borderColor: 'divider' },
                    }}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      skipHtml
                      components={{ a: ({ children }) => <>{children}</> }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </Box>
                ) : (
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{message.content}</Typography>
                )}
              </Box>
            ))}
            {asking && (
              <Box sx={{ alignSelf: 'flex-start', px: 1.5, py: 1.1 }}>
                <CircularProgress size={18} />
              </Box>
            )}
            {!asking && links.length > 0 && (
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ alignSelf: 'flex-start' }}>
                {links.map((link) => (
                  <Button
                    key={link.path}
                    component={Link}
                    to={link.path}
                    size="small"
                    variant="outlined"
                    endIcon={<ArrowForwardRoundedIcon fontSize="small" />}
                    onClick={() => setAnchorEl(null)}
                  >
                    {link.label}
                  </Button>
                ))}
              </Stack>
            )}
          </Box>
          {error && <Typography color="error" variant="caption" display="block" sx={{ mt: 1 }}>{error}</Typography>}
          <Box
            component="form"
            onSubmit={(event) => { event.preventDefault(); void handleSubmit() }}
            sx={{ display: 'flex', gap: 1, mt: 1.5, alignItems: 'flex-start' }}
          >
            <TextField
              fullWidth
              size="small"
              label="Ask a question"
              placeholder="Ask about a feature or where to find it..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              disabled={asking}
            />
            <Button type="submit" variant="contained" disabled={asking || question.trim().length < 3} sx={{ minWidth: 64, minHeight: 40 }}>
              Send
            </Button>
          </Box>
          {run && (
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1.25 }}>
              {run.model} / {run.input_tokens + run.output_tokens} tokens / {(run.latency_ms / 1000).toFixed(1)}s
              {Object.keys(run.redaction_counts).length > 0 && ' / PII protected before AI call'}
            </Typography>
          )}
        </Box>
      </Popover>
    </>
  )
}
