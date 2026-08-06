import { useState, useEffect } from 'react'
import { simulatorAPI, polesAPI } from '../services/api'
import { AlertTriangle, Zap, Settings, Play, RotateCcw, RefreshCw } from 'lucide-react'

export default function FaultSimulator() {
  const [networkStats, setNetworkStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [faultType, setFaultType] = useState('span')
  const [targetId, setTargetId] = useState('')
  const [startPole, setStartPole] = useState('')
  const [endPole, setEndPole] = useState('')
  const [activeFaults, setActiveFaults] = useState([])
  const [noiseDeviceId, setNoiseDeviceId] = useState('')
  const [noiseType, setNoiseType] = useState('dead_sensor')
  const [message, setMessage] = useState(null)

  useEffect(() => {
    loadNetworkStats()
  }, [])

  const loadNetworkStats = async () => {
    try {
      const poles = await polesAPI.getAll({ limit: 1 })
      const transformers = await polesAPI.getTransformers()
      setNetworkStats({
        poles: poles.headers['x-total-count'] || 0,
        transformers: transformers.data.length
      })
    } catch (error) {
      console.error('Error loading network stats:', error)
    }
  }

  const generateNetwork = async () => {
    setLoading(true)
    try {
      const response = await simulatorAPI.generateNetwork({
        num_transformers: 20,
        poles_per_dt: 70
      })
      setNetworkStats(response.data)
      setMessage({ type: 'success', text: `Network generated: ${response.data.transformers} DTs, ${response.data.poles} poles` })
      loadNetworkStats()
    } catch (error) {
      console.error('Error generating network:', error)
      setMessage({ type: 'error', text: 'Failed to generate network' })
    }
    setLoading(false)
  }

  const injectFault = async () => {
    setLoading(true)
    try {
      const payload = {
        fault_type: faultType,
        target_id: targetId
      }
      
      if (faultType === 'span') {
        payload.start_pole_id = startPole
        payload.end_pole_id = endPole
      }
      
      const response = await simulatorAPI.injectFault(payload)
      setActiveFaults([...activeFaults, response.data])
      setMessage({ type: 'success', text: response.data.message })
    } catch (error) {
      console.error('Error injecting fault:', error)
      setMessage({ type: 'error', text: 'Failed to inject fault: ' + (error.response?.data?.detail || error.message) })
    }
    setLoading(false)
  }

  const injectNoise = async () => {
    setLoading(true)
    try {
      const response = await simulatorAPI.injectNoise({
        device_id: noiseDeviceId,
        noise_type: noiseType
      })
      setMessage({ type: 'success', text: response.data.message })
    } catch (error) {
      console.error('Error injecting noise:', error)
      setMessage({ type: 'error', text: 'Failed to inject noise' })
    }
    setLoading(false)
  }

  const repairFault = async (faultId) => {
    setLoading(true)
    try {
      const response = await simulatorAPI.repairFault(faultId)
      setActiveFaults(activeFaults.filter(f => f.fault_id !== faultId))
      setMessage({ type: 'success', text: response.data.message })
    } catch (error) {
      console.error('Error repairing fault:', error)
      setMessage({ type: 'error', text: 'Failed to repair fault' })
    }
    setLoading(false)
  }

  const resetSimulator = async () => {
    setLoading(true)
    try {
      await simulatorAPI.reset()
      setActiveFaults([])
      setMessage({ type: 'success', text: 'Simulator reset complete' })
    } catch (error) {
      console.error('Error resetting simulator:', error)
      setMessage({ type: 'error', text: 'Failed to reset simulator' })
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fault Simulator</h1>
        <p className="text-gray-600 mt-1">Inject faults and noise to test the detection system</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${
          message.type === 'success' ? 'bg-success-50 text-success-800 border border-success-200' :
          'bg-danger-50 text-danger-800 border border-danger-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Network Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Transformers</p>
              <p className="text-2xl font-bold text-gray-900">{networkStats?.transformers || 0}</p>
            </div>
            <Zap className="h-8 w-8 text-primary-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Poles</p>
              <p className="text-2xl font-bold text-gray-900">{networkStats?.poles || 0}</p>
            </div>
            <Settings className="h-8 w-8 text-primary-600" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Faults</p>
              <p className="text-2xl font-bold text-danger-600">{activeFaults.length}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-danger-600" />
          </div>
        </div>
      </div>

      {/* Network Generation */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Network Generation</h2>
        <div className="flex items-center space-x-4">
          <button
            onClick={generateNetwork}
            disabled={loading}
            className="btn btn-primary flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Generate Synthetic Network
          </button>
          <button
            onClick={resetSimulator}
            disabled={loading}
            className="btn btn-danger flex items-center"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset Simulator
          </button>
        </div>
      </div>

      {/* Fault Injection */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Inject Fault</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fault Type</label>
            <select
              value={faultType}
              onChange={(e) => setFaultType(e.target.value)}
              className="select"
            >
              <option value="span">Span Fault</option>
              <option value="distribution_transformer">Distribution Transformer Fault</option>
              <option value="feeder">Feeder Fault</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {faultType === 'span' ? 'Start Pole ID' :
               faultType === 'distribution_transformer' ? 'Transformer ID' :
               'Feeder ID'}
            </label>
            <input
              type="text"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              placeholder={faultType === 'span' ? 'P-0001001' :
                          faultType === 'distribution_transformer' ? 'D-0001' :
                          'F-07-03'}
              className="input"
            />
          </div>

          {faultType === 'span' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Pole ID</label>
              <input
                type="text"
                value={endPole}
                onChange={(e) => setEndPole(e.target.value)}
                placeholder="P-0001002"
                className="input"
              />
            </div>
          )}

          <button
            onClick={injectFault}
            disabled={loading}
            className="btn btn-danger flex items-center"
          >
            <Play className="h-4 w-4 mr-2" />
            Inject Fault
          </button>
        </div>
      </div>

      {/* Noise Injection */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Inject Noise</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Device ID</label>
            <input
              type="text"
              value={noiseDeviceId}
              onChange={(e) => setNoiseDeviceId(e.target.value)}
              placeholder="KSPDB-F-07-03-D-0001-0001"
              className="input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Noise Type</label>
            <select
              value={noiseType}
              onChange={(e) => setNoiseType(e.target.value)}
              className="select"
            >
              <option value="dead_sensor">Dead Sensor</option>
              <option value="duplicate">Duplicate Telemetry</option>
              <option value="out_of_order">Out of Order Message</option>
            </select>
          </div>

          <button
            onClick={injectNoise}
            disabled={loading}
            className="btn btn-primary flex items-center"
          >
            <Settings className="h-4 w-4 mr-2" />
            Inject Noise
          </button>
        </div>
      </div>

      {/* Active Faults */}
      {activeFaults.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Faults</h2>
          <div className="space-y-3">
            {activeFaults.map((fault, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{fault.type.replace('_', ' ').toUpperCase()}</p>
                  <p className="text-sm text-gray-600">{fault.message}</p>
                </div>
                <button
                  onClick={() => repairFault(fault.fault_id)}
                  disabled={loading}
                  className="btn btn-success text-sm"
                >
                  Repair
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
