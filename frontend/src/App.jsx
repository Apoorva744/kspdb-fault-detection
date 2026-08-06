import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import OperatorConsole from './pages/OperatorConsole'
import FaultSimulator from './pages/FaultSimulator'
import { AlertTriangle, Activity, Zap } from 'lucide-react'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Zap className="h-8 w-8 text-primary-600 mr-2" />
                <span className="text-xl font-bold text-gray-900">KSPDB Fault Detection</span>
              </div>
              <div className="flex items-center space-x-4">
                <Link
                  to="/"
                  className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50"
                >
                  <Activity className="h-4 w-4 mr-1" />
                  Console
                </Link>
                <Link
                  to="/simulator"
                  className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-primary-600 hover:bg-gray-50"
                >
                  <AlertTriangle className="h-4 w-4 mr-1" />
                  Simulator
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<OperatorConsole />} />
            <Route path="/simulator" element={<FaultSimulator />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
