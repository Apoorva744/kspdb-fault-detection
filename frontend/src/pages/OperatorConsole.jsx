import { useState, useEffect } from 'react'
import { ticketsAPI, polesAPI } from '../services/api'
import { MapPin, AlertTriangle, CheckCircle, Clock, Users, Zap } from 'lucide-react'
import { format } from 'date-fns'

export default function OperatorConsole() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTicket, setSelectedTicket] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    loadTickets()
    const interval = setInterval(loadTickets, 10000) // Poll every 10 seconds
    return () => clearInterval(interval)
  }, [filter])

  const loadTickets = async () => {
    try {
      const params = filter !== 'all' ? { status: filter } : {}
      const response = await ticketsAPI.getAll(params)
      setTickets(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error loading tickets:', error)
      setLoading(false)
    }
  }

  const updateTicketStatus = async (ticketId, newStatus) => {
    try {
      await ticketsAPI.update(ticketId, { status: newStatus })
      loadTickets()
      if (selectedTicket?.ticket_id === ticketId) {
        setSelectedTicket(null)
      }
    } catch (error) {
      console.error('Error updating ticket:', error)
      alert('Failed to update ticket. Please check if restoration is verified.')
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      detected: 'bg-danger-100 text-danger-800 border-danger-200',
      acknowledged: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      crew_assigned: 'bg-blue-100 text-blue-800 border-blue-200',
      resolved: 'bg-purple-100 text-purple-800 border-purple-200',
      verified: 'bg-success-100 text-success-800 border-success-200',
      closed: 'bg-gray-100 text-gray-800 border-gray-200',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusIcon = (status) => {
    const icons = {
      detected: AlertTriangle,
      acknowledged: Clock,
      crew_assigned: Users,
      resolved: Zap,
      verified: CheckCircle,
      closed: CheckCircle,
    }
    const Icon = icons[status] || AlertTriangle
    return <Icon className="h-4 w-4" />
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-success-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-danger-600'
  }

  const filteredTickets = tickets.filter(t => 
    filter === 'all' || t.status === filter
  )

  const activeTickets = tickets.filter(t => 
    ['detected', 'acknowledged', 'crew_assigned', 'resolved'].includes(t.status)
  ).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Operator Console</h1>
          <p className="text-gray-600 mt-1">Real-time fault monitoring and ticket management</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-600">Active Incidents</p>
            <p className="text-2xl font-bold text-danger-600">{activeTickets}</p>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 border-b">
        {['all', 'detected', 'acknowledged', 'crew_assigned', 'resolved', 'verified', 'closed'].map(status => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
              filter === status
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {status.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ticket List */}
        <div className="lg:col-span-2 space-y-4">
          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading tickets...</div>
          ) : filteredTickets.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No tickets found</p>
            </div>
          ) : (
            filteredTickets.map(ticket => (
              <div
                key={ticket.id}
                className={`card cursor-pointer transition-all hover:shadow-lg ${
                  selectedTicket?.id === ticket.id ? 'ring-2 ring-primary-500' : ''
                }`}
                onClick={() => setSelectedTicket(ticket)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(ticket.status)}`}>
                        {getStatusIcon(ticket.status)}
                        <span className="ml-1 capitalize">{ticket.status.replace('_', ' ')}</span>
                      </span>
                      <span className="text-sm text-gray-500">{ticket.ticket_id}</span>
                    </div>
                    
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {ticket.fault_type.replace('_', ' ').toUpperCase()} Fault
                    </h3>
                    
                    <div className="flex items-center text-sm text-gray-600 mb-2">
                      <MapPin className="h-4 w-4 mr-1" />
                      {ticket.fault_location}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span className="flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        {ticket.affected_poles_count} poles
                      </span>
                      <span className={`flex items-center font-medium ${getConfidenceColor(ticket.confidence)}`}>
                        Confidence: {(ticket.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    
                    {ticket.ai_summary && (
                      <p className="mt-3 text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                        {ticket.ai_summary}
                      </p>
                    )}
                  </div>
                  
                  <div className="text-right text-sm text-gray-500">
                    <p>{format(new Date(ticket.detected_at), 'MMM d, HH:mm')}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Ticket Detail Panel */}
        <div className="lg:col-span-1">
          {selectedTicket ? (
            <div className="card sticky top-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Ticket Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Ticket ID</label>
                  <p className="text-gray-900">{selectedTicket.ticket_id}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Status</label>
                  <p className="capitalize">{selectedTicket.status.replace('_', ' ')}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Fault Type</label>
                  <p className="capitalize">{selectedTicket.fault_type.replace('_', ' ')}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Location</label>
                  <p className="text-gray-900">{selectedTicket.fault_location}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Coordinates</label>
                  <p className="text-gray-900 text-sm">
                    {selectedTicket.lat.toFixed(6)}, {selectedTicket.lon.toFixed(6)}
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">PIN Code</label>
                  <p className="text-gray-900">{selectedTicket.pincode || 'Unknown'}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Affected Poles</label>
                  <p className="text-gray-900">{selectedTicket.affected_poles_count}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Confidence</label>
                  <p className={`font-medium ${getConfidenceColor(selectedTicket.confidence)}`}>
                    {(selectedTicket.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Reason</label>
                  <p className="text-sm text-gray-700">{selectedTicket.confidence_reason}</p>
                </div>
                
                <div className="pt-4 border-t">
                  <label className="text-sm font-medium text-gray-600 mb-2 block">Actions</label>
                  <div className="space-y-2">
                    {selectedTicket.status === 'detected' && (
                      <button
                        onClick={() => updateTicketStatus(selectedTicket.ticket_id, 'acknowledged')}
                        className="w-full btn btn-primary"
                      >
                        Acknowledge
                      </button>
                    )}
                    {selectedTicket.status === 'acknowledged' && (
                      <button
                        onClick={() => updateTicketStatus(selectedTicket.ticket_id, 'crew_assigned')}
                        className="w-full btn btn-primary"
                      >
                        Assign Crew
                      </button>
                    )}
                    {selectedTicket.status === 'crew_assigned' && (
                      <button
                        onClick={() => updateTicketStatus(selectedTicket.ticket_id, 'resolved')}
                        className="w-full btn btn-success"
                      >
                        Mark Resolved
                      </button>
                    )}
                    {selectedTicket.status === 'verified' && (
                      <button
                        onClick={() => updateTicketStatus(selectedTicket.ticket_id, 'closed')}
                        className="w-full btn btn-primary"
                      >
                        Close Ticket
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card text-center py-8 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Select a ticket to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
