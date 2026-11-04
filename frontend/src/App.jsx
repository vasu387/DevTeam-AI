/**
 * App - Root component. Handles simple client-side page routing.
 */

import { useState } from 'react'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import Agents from './pages/Agents'
import Settings from './pages/Settings'

const PAGES = {
  dashboard: Dashboard,
  projects: Projects,
  agents: Agents,
  settings: Settings,
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')

  const PageComponent = PAGES[activePage] || Dashboard

  return (
    <MainLayout activePage={activePage} onNavigate={setActivePage}>
      <PageComponent onNavigate={setActivePage} />
    </MainLayout>
  )
}

