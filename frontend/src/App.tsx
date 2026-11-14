import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Budget } from './pages/Budget'
import { Categories } from './pages/Categories'
import { Dashboard } from './pages/Dashboard'
import { FixedExpenses } from './pages/FixedExpenses'
import { Import } from './pages/Import'
import { Income } from './pages/Income'
import { Stats } from './pages/Stats'
import { Transactions } from './pages/Transactions'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="income" element={<Income />} />
        <Route path="fixed" element={<FixedExpenses />} />
        <Route path="stats" element={<Stats />} />
        <Route path="categories" element={<Categories />} />
        <Route path="budget" element={<Budget />} />
        <Route path="import" element={<Import />} />
      </Route>
    </Routes>
  )
}

export default App
