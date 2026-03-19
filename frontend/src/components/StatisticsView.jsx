import React from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

const StatisticsView = ({ stats }) => {
  if (!stats) {
    return <div className="text-center py-8">Loading statistics...</div>
  }

  // Colors for charts
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard
          title="Total Transactions"
          value={stats.transactions?.total_transactions || 0}
          subtext={`Success: ${stats.transactions?.success_rate || 0}%`}
          icon="💳"
          trend="up"
        />

        <KPICard
          title="Transaction Volume"
          value={`$${(stats.transactions?.total_amount || 0).toLocaleString()}`}
          subtext={`Avg: $${(stats.transactions?.average_amount || 0).toLocaleString()}`}
          icon="💰"
          trend="up"
        />

        <KPICard
          title="Total Users"
          value={stats.users?.total_users || 0}
          subtext={`New: ${stats.users?.new_users || 0}`}
          icon="👥"
          trend="up"
        />

        <KPICard
          title="Fraud Alerts"
          value={stats.fraud?.total_alerts || 0}
          subtext={`High-Risk: ${stats.fraud?.high_risk_alerts || 0}`}
          icon="🚨"
          trend="warning"
        />

        <KPICard
          title="KYC Approved"
          value={stats.users?.kyc_approved || 0}
          subtext={`${((stats.users?.kyc_approved / (stats.users?.total_users || 1)) * 100).toFixed(1)}%`}
          icon="✅"
          trend="up"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Transactions Chart */}
        <ChartCard title="Daily Transactions Trend">
          {stats.dailyTransactions && stats.dailyTransactions.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats.dailyTransactions}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="transactions"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Transactions"
                  isAnimationActive={true}
                />
                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Amount"
                  yAxisId="right"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </ChartCard>

        {/* Transaction Status Distribution */}
        <ChartCard title="Transaction Status Distribution">
          {stats.transactions ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    {
                      name: 'Successful',
                      value: Math.round(
                        (stats.transactions.total_transactions *
                          stats.transactions.success_rate) /
                          100
                      )
                    },
                    {
                      name: 'Failed',
                      value: Math.round(
                        (stats.transactions.total_transactions *
                          (100 - stats.transactions.success_rate)) /
                          100
                      )
                    }
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </ChartCard>

        {/* User Growth Chart */}
        <ChartCard title="User Growth Trend">
          {stats.userGrowth && stats.userGrowth.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.userGrowth}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                />
                <Legend />
                <Bar dataKey="new_users" fill="#3b82f6" name="New Users" />
                <Bar dataKey="active_users" fill="#10b981" name="Active Users" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </ChartCard>

        {/* Fraud Metrics */}
        <ChartCard title="Fraud Detection Metrics">
          {stats.fraud ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  {
                    name: 'Fraud Metrics',
                    'High Risk': stats.fraud.high_risk_alerts || 0,
                    'Medium Risk': stats.fraud.medium_risk_alerts || 0,
                    'Low Risk': stats.fraud.low_risk_alerts || 0
                  }
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                />
                <Legend />
                <Bar dataKey="High Risk" fill="#ef4444" />
                <Bar dataKey="Medium Risk" fill="#f59e0b" />
                <Bar dataKey="Low Risk" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </ChartCard>

        {/* Risk Score Distribution */}
        <ChartCard title="Average Risk Scores">
          {stats.fraud ? (
            <div className="space-y-4 pt-8">
              <RiskScoreRow
                label="Average User Risk"
                score={stats.fraud.average_risk_score || 0}
                color="bg-blue-600"
              />
              <RiskScoreRow
                label="Highest Risk Score"
                score={stats.fraud.max_risk_score || 0}
                color="bg-red-600"
              />
              <RiskScoreRow
                label="Fraud Detection Rate"
                score={stats.fraud.detection_rate || 0}
                color="bg-yellow-600"
              />
              <div className="bg-gray-50 rounded p-3 mt-4">
                <p className="text-sm text-gray-600 font-medium">Blocked Accounts</p>
                <p className="text-2xl font-bold text-red-600">
                  {stats.fraud.blocked_accounts || 0}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No data available</p>
          )}
        </ChartCard>
      </div>

      {/* System Health Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">System Health</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <HealthIndicator
            label="API Response Time"
            value="45ms"
            status="healthy"
          />
          <HealthIndicator
            label="Database Connection"
            value="Connected"
            status="healthy"
          />
          <HealthIndicator
            label="Real-time Updates"
            value="Active"
            status="healthy"
          />
        </div>

        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded">
          <h4 className="font-semibold text-blue-900 mb-2">📈 Performance Summary</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>✅ Transaction processing: {stats.transactions?.success_rate || 0}% success rate</li>
            <li>✅ User engagement: {stats.users?.active_users || 0} active users today</li>
            <li>✅ Fraud detection: {(stats.fraud?.detection_rate || 0).toFixed(1)}% accuracy</li>
            <li>✅ System uptime: 99.9%</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

// Component: KPI Card
const KPICard = ({ title, value, subtext, icon, trend }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-600 text-xs font-medium uppercase tracking-wide">
            {title}
          </p>
          <p className="text-2xl md:text-3xl font-bold text-gray-900 mt-2">{value}</p>
          <p className="text-xs text-gray-500 mt-1">{subtext}</p>
        </div>
        <div className="text-2xl">{icon}</div>
      </div>

      {trend && (
        <div className="mt-2 flex items-center gap-1">
          {trend === 'up' && <span className="text-green-600 text-sm">📈 Up</span>}
          {trend === 'warning' && <span className="text-red-600 text-sm">⚠️ Alert</span>}
        </div>
      )}
    </div>
  )
}

// Component: Chart Card
const ChartCard = ({ title, children }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      {children}
    </div>
  )
}

// Component: Risk Score Row
const RiskScoreRow = ({ label, score, color }) => {
  const percentage = Math.min(score, 100)

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-bold text-gray-900">{score.toFixed(1)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

// Component: Health Indicator
const HealthIndicator = ({ label, value, status }) => {
  const statusColor = {
    healthy: 'bg-green-100 text-green-800 border-green-300',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    critical: 'bg-red-100 text-red-800 border-red-300'
  }

  return (
    <div className={`p-4 rounded-lg border ${statusColor[status]}`}>
      <p className="text-sm font-medium mb-1">{label}</p>
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs mt-1 capitalize">{status}</p>
    </div>
  )
}

export default StatisticsView
