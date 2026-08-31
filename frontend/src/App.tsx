import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Budget } from './pages/Budget'
import { Categories } from './pages/Categories'
import { Dashboard } from './pages/Dashboard'
import { Import } from './pages/Import'
import { Transactions } from './pages/Transactions'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="categories" element={<Categories />} />
        <Route path="budget" element={<Budget />} />
        <Route path="import" element={<Import />} />
      </Route>
    </Routes>
  )
}

export default App
