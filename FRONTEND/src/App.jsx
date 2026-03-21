import { useState, useEffect } from 'react'
import TabNav from './components/TabNav/TabNav'
import ScrollToTop from './components/ScrollToTop/ScrollToTop'
import DashboardTab from './tabs/DashboardTab/DashboardTab'
import TicketsTab from './tabs/TicketsTab/TicketsTab'
import InventoryTab from './tabs/InventoryTab/InventoryTab'
import CleaningTab from './tabs/CleaningTab/CleaningTab'
import HaccpTab from './tabs/HaccpTab/HaccpTab'
import ScheduleTab from './tabs/ScheduleTab/ScheduleTab'
import ProductsTab from './tabs/ProductsTab/ProductsTab'
import PurchasesTab from './tabs/PurchasesTab/PurchasesTab'
import CookingPlanTab from './tabs/CookingPlanTab/CookingPlanTab'
import AnalysisTab from './tabs/AnalysisTab/AnalysisTab'
import './App.css'

function useClock() {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return time
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const clock = useClock()

  const timeStr = clock.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const dateStr = clock.toLocaleDateString([], {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  return (
    <>
      <header className="dashboard-header">
        <button
          className="dashboard-title dashboard-title--btn"
          onClick={() => setActiveTab('dashboard')}
        >
          <h1>Bako Bakery</h1>
          <span>Operations Dashboard</span>
        </button>
        <div className="dashboard-clock">
          {dateStr} &nbsp;·&nbsp; {timeStr}
        </div>
      </header>

      <div className="dashboard-content">
        <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

        <main className="tab-content" role="tabpanel">
          {activeTab === 'dashboard'  && <DashboardTab onNavigate={setActiveTab} />}
          {activeTab === 'tickets'    && <TicketsTab />}
          {activeTab === 'inventory'  && <InventoryTab />}
          {activeTab === 'cleaning'   && <CleaningTab />}
          {activeTab === 'haccp'        && <HaccpTab />}
          {activeTab === 'schedule'     && <ScheduleTab />}
          {activeTab === 'products'     && <ProductsTab />}
          {activeTab === 'purchases'    && <PurchasesTab />}
          {activeTab === 'cooking-plan' && <CookingPlanTab />}
          {activeTab === 'analysis'     && <AnalysisTab />}
        </main>
      </div>

      <ScrollToTop />
    </>
  )
}

export default App
