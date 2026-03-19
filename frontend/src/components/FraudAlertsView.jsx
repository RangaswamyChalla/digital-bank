import { useState, useEffect } from 'react'
import analyticsService from '../services/analyticsService'

const FraudAlertsView = ({ alerts: initialAlerts, onAlertUpdate }) => {
  const [alerts, setAlerts] = useState(initialAlerts || [])
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterRisk, setFilterRisk] = useState('all')
  const [actionMessage, setActionMessage] = useState(null)

  // Update alerts when props change
  useEffect(() => {
    setAlerts(initialAlerts || [])
  }, [initialAlerts])

  // Handle alert action (block, mark safe, escalate)
  const handleAlertAction = async (alertId, action) => {
    setActionLoading(true)
    setActionMessage(null)

    try {
      await analyticsService.takeAlertAction(
        alertId,
        action,
        `Admin action: ${action} - ${new Date().toLocaleString()}`
      )

      // Update alert in list
      setAlerts(prev =>
        prev.map(alert =>
          alert.id === alertId
            ? { ...alert, status: action === 'block' ? 'blocked' : 'verified_safe', admin_action: action }
            : alert
        )
      )

      // Close details panel
      setSelectedAlert(null)

      // Show success message
      setActionMessage({
        type: 'success',
        text: `Alert ${action.replace('_', ' ')} successfully`
      })

      // Refresh data
      if (onAlertUpdate) {
        setTimeout(onAlertUpdate, 1000)
      }

      // Clear message after 3 seconds
      setTimeout(() => setActionMessage(null), 3000)
    } catch (error) {
      console.error('Failed to take action:', error)
      setActionMessage({
        type: 'error',
        text: `Failed to take action: ${error.message}`
      })
    } finally {
      setActionLoading(false)
    }
  }

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    if (filterStatus !== 'all' && alert.status !== filterStatus) return false
    if (filterRisk !== 'all' && alert.risk_level !== filterRisk) return false
    return true
  })

  // Stats
  const openAlerts = alerts.filter(a => a.status === 'open').length
  const highRiskAlerts = alerts.filter(a => a.risk_level === 'high').length
  const blockedAlerts = alerts.filter(a => a.status === 'blocked').length

  return (
    <div className="space-y-6">
      {/* Action Message */}
      {actionMessage && (
        <div
          className={`p-4 rounded-lg ${
            actionMessage.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          {actionMessage.text}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Total Alerts" value={alerts.length} color="blue" />
        <StatCard label="Open Alerts" value={openAlerts} color="red" highlight={openAlerts > 0} />
        <StatCard label="High Risk" value={highRiskAlerts} color="orange" />
        <StatCard label="Blocked" value={blockedAlerts} color="gray" />
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col md:flex-row gap-3 bg-white rounded-lg shadow p-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Filter by Status
          </label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="verified_safe">Verified Safe</option>
            <option value="blocked">Blocked</option>
            <option value="escalated">Escalated</option>
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Filter by Risk Level
          </label>
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={() => {
              setFilterStatus('all')
              setFilterRisk('all')
            }}
            className="w-full md:w-auto bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 text-sm font-medium"
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50">
              <h3 className="font-semibold text-gray-900">
                Fraud Alerts {filteredAlerts.length > 0 && `(${filteredAlerts.length})`}
              </h3>
            </div>

            {filteredAlerts.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500">No alerts found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-3 text-left font-semibold text-gray-700">
                        Date/Time
                      </th>
                      <th className="px-6 py-3 text-left font-semibold text-gray-700">
                        User ID
                      </th>
                      <th className="px-6 py-3 text-left font-semibold text-gray-700">
                        Risk Level
                      </th>
                      <th className="px-6 py-3 text-left font-semibold text-gray-700">
                        Score
                      </th>
                      <th className="px-6 py-3 text-left font-semibold text-gray-700">
                        Status
                      </th>
                      <th className="px-6 py-3 text-center font-semibold text-gray-700">
                        Action
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y">
                    {filteredAlerts.map((alert) => (
                      <tr
                        key={alert.id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedAlert(alert)}
                      >
                        <td className="px-6 py-4 text-gray-900">
                          {new Date(alert.created_at || Date.now()).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {alert.user_id}
                        </td>
                        <td className="px-6 py-4">
                          <RiskBadge level={alert.risk_level} />
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-gray-200 rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${
                                  alert.risk_score >= 70
                                    ? 'bg-red-600'
                                    : alert.risk_score >= 40
                                    ? 'bg-yellow-600'
                                    : 'bg-green-600'
                                }`}
                                style={{ width: `${alert.risk_score}%` }}
                              />
                            </div>
                            <span className="font-semibold text-gray-900">
                              {alert.risk_score.toFixed(0)}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={alert.status} />
                        </td>
                        <td className="px-6 py-4 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedAlert(alert)
                            }}
                            className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                          >
                            Review →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Alert Details Panel */}
        <div>
          {selectedAlert ? (
            <div className="bg-white rounded-lg shadow overflow-hidden sticky top-6">
              <div className="px-6 py-4 bg-gradient-to-r from-red-600 to-red-700 text-white">
                <h3 className="font-semibold text-lg">Alert Details</h3>
                <p className="text-sm text-red-100 mt-1">ID: {selectedAlert.id}</p>
              </div>

              <div className="p-6 space-y-4">
                {/* Risk Score */}
                <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-lg p-4 border border-red-200">
                  <p className="text-red-900 text-sm font-medium mb-1">Risk Score</p>
                  <div className="flex items-end gap-2">
                    <p className="text-4xl font-bold text-red-600">
                      {selectedAlert.risk_score.toFixed(1)}
                    </p>
                    <p className="text-red-700 font-semibold mb-1">/100</p>
                  </div>
                  <div className="w-full bg-red-200 rounded-full h-2 mt-3">
                    <div
                      className="h-2 rounded-full bg-red-600"
                      style={{ width: `${selectedAlert.risk_score}%` }}
                    />
                  </div>
                </div>

                {/* Risk Level */}
                <div>
                  <p className="text-gray-700 text-sm font-medium mb-2">Risk Level</p>
                  <RiskBadge level={selectedAlert.risk_level} large />
                </div>

                {/* Status */}
                <div>
                  <p className="text-gray-700 text-sm font-medium mb-2">Status</p>
                  <StatusBadge status={selectedAlert.status} large />
                </div>

                {/* User Info */}
                <div>
                  <p className="text-gray-700 text-sm font-medium mb-2">User Information</p>
                  <div className="bg-gray-50 rounded p-3 text-sm space-y-1">
                    <p>
                      <span className="text-gray-600">User ID:</span> {selectedAlert.user_id}
                    </p>
                    {selectedAlert.transaction_id && (
                      <p>
                        <span className="text-gray-600">Transaction:</span>{' '}
                        {selectedAlert.transaction_id}
                      </p>
                    )}
                  </div>
                </div>

                {/* Reasons */}
                {selectedAlert.reasons && selectedAlert.reasons.length > 0 && (
                  <div>
                    <p className="text-gray-700 text-sm font-medium mb-2">Detection Reasons</p>
                    <ul className="space-y-2">
                      {selectedAlert.reasons.map((reason, idx) => (
                        <li key={idx} className="flex gap-2 text-sm text-gray-700">
                          <span className="text-red-600 font-bold">•</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommended Action */}
                <div>
                  <p className="text-gray-700 text-sm font-medium mb-2">Recommended Action</p>
                  <div className="bg-blue-50 rounded p-3 border border-blue-200">
                    <p className="text-blue-900 font-semibold text-sm">
                      {selectedAlert.recommended_action?.replace('_', ' ').toUpperCase()}
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                {selectedAlert.status === 'open' && (
                  <div className="space-y-2 pt-4 border-t">
                    <button
                      onClick={() => handleAlertAction(selectedAlert.id, 'block')}
                      disabled={actionLoading}
                      className="w-full bg-red-600 text-white py-2 px-3 rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium text-sm transition"
                    >
                      {actionLoading ? '⏳ Processing...' : '🚫 Block Account'}
                    </button>

                    <button
                      onClick={() => handleAlertAction(selectedAlert.id, 'verify_safe')}
                      disabled={actionLoading}
                      className="w-full bg-green-600 text-white py-2 px-3 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium text-sm transition"
                    >
                      {actionLoading ? '⏳ Processing...' : '✅ Mark Safe'}
                    </button>

                    <button
                      onClick={() => handleAlertAction(selectedAlert.id, 'escalate')}
                      disabled={actionLoading}
                      className="w-full bg-orange-600 text-white py-2 px-3 rounded-lg hover:bg-orange-700 disabled:opacity-50 font-medium text-sm transition"
                    >
                      {actionLoading ? '⏳ Processing...' : '⬆️ Escalate'}
                    </button>
                  </div>
                )}

                {selectedAlert.status !== 'open' && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded">
                    <p className="text-amber-900 text-sm">
                      ⚠️ This alert has already been actioned. Status:{' '}
                      <span className="font-semibold">{selectedAlert.status}</span>
                    </p>
                  </div>
                )}

                {/* Admin Notes */}
                {selectedAlert.admin_notes && (
                  <div>
                    <p className="text-gray-700 text-sm font-medium mb-2">Admin Notes</p>
                    <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 italic">
                      {selectedAlert.admin_notes}
                    </div>
                  </div>
                )}

                {/* Close Button */}
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="w-full mt-4 py-2 px-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-medium text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
              <p className="text-sm">Select an alert to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Component: Risk Badge
const RiskBadge = ({ level, large = false }) => {
  const colors = {
    high: 'bg-red-100 text-red-800 border-red-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-green-100 text-green-800 border-green-300'
  }

  const icons = {
    high: '🔴',
    medium: '🟡',
    low: '🟢'
  }

  return (
    <span
      className={`inline-flex items-center gap-1 border rounded px-3 py-1 font-medium ${
        colors[level]
      } ${large ? 'text-base px-4 py-2' : 'text-sm'}`}
    >
      {icons[level]} {level.toUpperCase()}
    </span>
  )
}

// Component: Status Badge
const StatusBadge = ({ status, large = false }) => {
  const colors = {
    open: 'bg-blue-100 text-blue-800 border-blue-300',
    verified_safe: 'bg-green-100 text-green-800 border-green-300',
    blocked: 'bg-red-100 text-red-800 border-red-300',
    escalated: 'bg-orange-100 text-orange-800 border-orange-300'
  }

  const icons = {
    open: '⏳',
    verified_safe: '✅',
    blocked: '🚫',
    escalated: '⬆️'
  }

  return (
    <span
      className={`inline-flex items-center gap-1 border rounded px-3 py-1 font-medium ${
        colors[status]
      } ${large ? 'text-base px-4 py-2' : 'text-sm'}`}
    >
      {icons[status]} {status.replace('_', ' ').toUpperCase()}
    </span>
  )
}

// Component: Stat Card
const StatCard = ({ label, value, color, highlight }) => {
  const colors = {
    blue: 'bg-blue-50 border-blue-200',
    red: 'bg-red-50 border-red-200',
    orange: 'bg-orange-50 border-orange-200',
    gray: 'bg-gray-50 border-gray-200'
  }

  const textColors = {
    blue: 'text-blue-600',
    red: 'text-red-600',
    orange: 'text-orange-600',
    gray: 'text-gray-600'
  }

  return (
    <div
      className={`border rounded-lg p-4 ${colors[color]} ${
        highlight ? 'ring-2 ring-red-400' : ''
      }`}
    >
      <p className="text-gray-600 text-sm font-medium">{label}</p>
      <p className={`text-3xl font-bold ${textColors[color]} mt-2`}>{value}</p>
    </div>
  )
}

export default FraudAlertsView
