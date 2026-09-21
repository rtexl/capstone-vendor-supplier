import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { MockErpSupplierPage } from './pages/MockErpSupplierPage'
import { SupplierIntakePage } from './pages/SupplierIntakePage'
import { SupplierPortalPage } from './pages/SupplierPortalPage'
import { SupplierReviewPage } from './pages/SupplierReviewPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/supplier" replace />} />
        <Route path="supplier" element={<DashboardPage mode="supplier" />} />
        <Route path="supplier/new" element={<SupplierIntakePage />} />
        <Route path="supplier/:supplierId" element={<SupplierPortalPage />} />
        <Route path="reviewer" element={<DashboardPage mode="reviewer" />} />
        <Route path="reviewer/:supplierId" element={<SupplierReviewPage />} />
        <Route path="reviewer/:supplierId/erp" element={<MockErpSupplierPage />} />
        <Route path="*" element={<Navigate to="/supplier" replace />} />
      </Route>
    </Routes>
  )
}
