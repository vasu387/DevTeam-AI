/**
 * MainLayout - Root layout with sidebar and main content area.
 */

import { useState } from 'react'
import Sidebar from '../components/Sidebar'

export default function MainLayout({ children, activePage, onNavigate }) {
  return (
    <div className="flex h-screen bg-obsidian-900 overflow-hidden">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />
      <main className="flex-1 flex flex-col overflow-hidden bg-grid">
        {children}
      </main>
    </div>
  )
}

