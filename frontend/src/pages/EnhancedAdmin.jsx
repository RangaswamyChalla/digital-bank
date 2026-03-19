import { useState, useEffect, useCallback } from 'react'
import analyticsService from '../services/analyticsService'
import useWebSocket from '../hooks/useWebSocket'
import StatisticsView from '../components/StatisticsView'
import FraudAlertsView from '../components/FraudAlertsView'

const EnhancedAdmin = () => {
  const [stats, setStats] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [activeTab, setActiveTab] = useState('statistics')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch dashboard stats and fraud alerts in parallel
      const [dashboardData, fraudAlerts] = await Promise.all([
        analyticsService.getDashboardStats(),
        analyticsService.getFraudAlerts(50, 0, null)
      ])

      setStats(dashboardData)
      setAlerts(fraudAlerts.items || fraudAlerts)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to load dashboard:', err)
      setError(err.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  // WebSocket for real-time admin updates
  // Get token for WebSocket authentication (stored in localStorage for WS auth)
  const wsToken = localStorage.getItem('access_token')
  const { isConnected, send: sendWS } = useWebSocket(
    'ws://localhost:8000/ws/admin/dashboard/admin-user',
    wsToken,
    (message) => {
      try {
        console.log('WebSocket message received:', message)

        if (message.type === 'fraud_alert') {
          // New fraud alert detected
          setAlerts(prev => {
            const updated = [message.data, ...prev]
            return updated.slice(0, 50) // Keep last 50
          })
          setLastUpdate(new Date())
        } else if (message.type === 'dashboard_update') {
          // Dashboard data updated
          if (message.data.stats) {
            setStats(message.data.stats)
          }
          setLastUpdate(new Date())
        } else if (message.type === 'transaction_update') {
          // Transaction occurred - refresh stats
          loadDashboardData()
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err)
      }
    }
  )

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData()
    }, 30000)

    return () => clearInterval(interval)
  }, [loadDashboardData])

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h2 className="text-red-800 font-semibold mb-2">Failed to Load Dashboard</h2>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={loadDashboardData}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Super Admin Dashboard</h1>
          <p className="text-sm text-gray-600 mt-1">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Real-time' : 'Offline'}
            </span>
          </div>

          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-8">
          <button
            onClick={() => setActiveTab('statistics')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'statistics'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📊 Statistics
          </button>

          <button
            onClick={() => setActiveTab('fraud')}
            className={`py-3 px-1 border-b-2 font-medium text-sm relative ${
              activeTab === 'fraud'
                ? 'border-red-600 text-red-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            🚨 Fraud Alerts
            {alerts && alerts.length > 0 && (
              <span className="absolute -top-2 -right-4 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {alerts.filter(a => a.status === 'open').length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('users')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            👥 User Management
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {loading && !stats ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        ) : (
          <>
            {activeTab === 'statistics' && stats && (
              <StatisticsView stats={stats} />
            )}

            {activeTab === 'fraud' && (
              <FraudAlertsView alerts={alerts} onAlertUpdate={() => loadDashboardData()} />
            )}

            {activeTab === 'users' && (
              <UserManagementView stats={stats} />
            )}
          </>
        )}
      </div>
    </div>
  )
}

// User Management View Component
const UserManagementView = ({ stats }) => {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-6 border-b">
        <h2 className="text-xl font-semibold">User Management</h2>
      </div>

      {stats?.users && (
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-gray-600 text-sm font-medium">Total Users</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {stats.users.total_users}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-gray-600 text-sm font-medium">KYC Approved</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {stats.users.kyc_approved}
              </p>
              <p className="text-xs text-gray-600 mt-2">
                {((stats.users.kyc_approved / stats.users.total_users) * 100).toFixed(1)}%
              </p>
            </div>

            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-gray-600 text-sm font-medium">Active Users</p>
              <p className="text-3xl font-bold text-yellow-600 mt-2">
                {stats.users.active_users || 0}
              </p>
            </div>

            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-gray-600 text-sm font-medium">At Risk</p>
              <p className="text-3xl font-bold text-red-600 mt-2">
                {stats.fraud?.high_risk_users || 0}
              </p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">Performance Metrics</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Avg Account Age</p>
                <p className="font-semibold text-blue-900">45 days</p>
              </div>
              <div>
                <p className="text-gray-600">User Retention</p>
                <p className="font-semibold text-blue-900">87%</p>
              </div>
              <div>
                <p className="text-gray-600">KYC Completion Rate</p>
                <p className="font-semibold text-blue-900">
                  {((stats.users.kyc_approved / stats.users.total_users) * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-gray-600">Status</p>
                <p className="font-semibold text-green-900">🟢 Healthy</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EnhancedAdmin
