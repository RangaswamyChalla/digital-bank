import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

const Dashboard = () => {
  const { user } = useAuth()
  const [totalBalance, setTotalBalance] = useState(0)
  const [accounts, setAccounts] = useState([])
  const [recentTransactions, setRecentTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [balanceRes, accountsRes, transactionsRes] = await Promise.all([
        api.get('/api/accounts/balance'),
        api.get('/api/accounts'),
        api.get('/api/transactions?limit=5')
      ])

      setTotalBalance(balanceRes.data.total_balance)
      setAccounts(accountsRes.data)
      setRecentTransactions(transactionsRes.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getKYCStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      submitted: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    }
    return styles[status] || 'bg-slate-100 text-slate-800'
  }

  const getTransactionIcon = (type) => {
    if (type === 'credit') {
      return (
        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </div>
      )
    }
    return (
      <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
        <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      </div>
    )
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const maskAccountNumber = (num) => {
    return '****' + num.slice(-4)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-800"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Welcome header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Welcome back, {user?.full_name?.split(' ')[0]}</h1>
          <p className="text-slate-500">Here's your financial overview</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">KYC Status:</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getKYCStatusBadge(user?.kyc_status)}`}>
            {user?.kyc_status?.toUpperCase() || 'PENDING'}
          </span>
        </div>
      </div>

      {/* Balance card */}
      <div className="bg-gradient-to-r from-primary-800 to-primary-600 rounded-2xl p-6 text-white">
        <p className="text-primary-100 text-sm mb-1">Total Balance</p>
        <p className="text-4xl font-bold">${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
        <p className="text-primary-100 text-sm mt-2">USD</p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p className="text-slate-500 text-sm">Total Accounts</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{accounts.length}</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p className="text-slate-500 text-sm">KYC Level</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{user?.kyc_level || 0}</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <p className="text-slate-500 text-sm">Recent Transactions</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{recentTransactions.length}</p>
        </div>
      </div>

      {/* Accounts list */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="p-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-800">Your Accounts</h2>
        </div>
        <div className="p-4 space-y-3">
          {accounts.length === 0 ? (
            <p className="text-slate-500 text-center py-4">No accounts yet. Create one to get started.</p>
          ) : (
            accounts.map((account) => (
              <div key={account.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-mono font-medium text-slate-800">{maskAccountNumber(account.account_number)}</p>
                  <p className="text-sm text-slate-500 capitalize">{account.account_type.replace('_', ' ')}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-slate-800">${Number(account.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                  <p className={`text-xs ${account.status === 'active' ? 'text-green-600' : 'text-red-600'}`}>
                    {account.status.toUpperCase()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Recent transactions */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="p-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-800">Recent Transactions</h2>
        </div>
        <div className="divide-y divide-slate-100">
          {recentTransactions.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No transactions yet</p>
          ) : (
            recentTransactions.map((tx) => (
              <div key={tx.id} className="p-4 flex items-center gap-4">
                {getTransactionIcon(tx.transaction_type)}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800 truncate">
                    {tx.transaction_type === 'credit' ? 'Received from' : 'Sent to'}{' '}
                    {tx.transaction_type === 'credit' ? tx.from_account_number : tx.to_account_number}
                  </p>
                  <p className="text-sm text-slate-500">{formatDate(tx.created_at)}</p>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${tx.transaction_type === 'credit' ? 'text-green-600' : 'text-red-600'}`}>
                    {tx.transaction_type === 'credit' ? '+' : '-'}${Number(tx.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </p>
                  <p className={`text-xs ${tx.status === 'completed' ? 'text-green-600' : 'text-yellow-600'}`}>
                    {tx.status.toUpperCase()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard