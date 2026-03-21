import { useState, useEffect } from 'react'
import TabNav from './components/TabNav/TabNav'
import TicketsTab from './tabs/TicketsTab/TicketsTab'
import InventoryTab from './tabs/InventoryTab/InventoryTab'
import CleaningTab from './tabs/CleaningTab/CleaningTab'
import HaccpTab from './tabs/HaccpTab/HaccpTab'
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
  const [activeTab, setActiveTab] = useState('tickets')
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
        <div className="dashboard-title">
          <h1>Bako Bakery</h1>
          <span>Operations Dashboard</span>
        </div>
        <div className="dashboard-clock">
          {dateStr} &nbsp;·&nbsp; {timeStr}
        </div>
      </header>

      <div className="dashboard-content">
        <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

        <main className="tab-content" role="tabpanel">
          {activeTab === 'tickets'   && <TicketsTab />}
          {activeTab === 'inventory' && <InventoryTab />}
          {activeTab === 'cleaning'  && <CleaningTab />}
          {activeTab === 'haccp'     && <HaccpTab />}
        </main>
      </div>
    </>
  )
}

export default App
