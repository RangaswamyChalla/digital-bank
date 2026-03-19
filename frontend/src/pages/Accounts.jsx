import { useState, useEffect } from 'react'
import api from '../services/api'

const Accounts = () => {
  const [accounts, setAccounts] = useState([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [formData, setFormData] = useState({
    account_type: 'savings',
    initial_deposit: '10'
  })
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await api.get('/accounts')
      setAccounts(response.data)
    } catch (error) {
      console.error('Failed to fetch accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setCreating(true)

    try {
      const response = await api.post('/accounts', {
        account_type: formData.account_type,
        initial_deposit: parseFloat(formData.initial_deposit)
      })

      setAccounts([...accounts, response.data])
      setSuccess('Account created successfully!')
      setShowCreateModal(false)
      setFormData({ account_type: 'savings', initial_deposit: '10' })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account')
    } finally {
      setCreating(false)
    }
  }

  const accountTypeLabels = {
    savings: 'Savings Account',
    checking: 'Checking Account',
    fixed_deposit: 'Fixed Deposit'
  }

  const accountTypeColors = {
    savings: 'bg-blue-100 text-blue-800',
    checking: 'bg-purple-100 text-purple-800',
    fixed_deposit: 'bg-amber-100 text-amber-800'
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Accounts</h1>
          <p className="text-slate-500">Manage your bank accounts</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-primary-800 hover:bg-primary-700 text-white rounded-lg font-medium btn-transition"
        >
          + Create Account
        </button>
      </div>

      {/* Error/Success messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}
      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-600">
          {success}
        </div>
      )}

      {/* Account cards */}
      {accounts.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
          <h3 className="text-lg font-semibold text-slate-800 mb-2">No accounts yet</h3>
          <p className="text-slate-500 mb-4">Create your first account to get started with banking</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary-800 hover:bg-primary-700 text-white rounded-lg font-medium btn-transition"
          >
            Create Account
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <div key={account.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${accountTypeColors[account.account_type]}`}>
                  {accountTypeLabels[account.account_type]}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${account.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {account.status.toUpperCase()}
                </span>
              </div>

              <p className="font-mono text-lg text-slate-600 mb-1">{account.account_number}</p>

              <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-sm text-slate-500">Available Balance</p>
                <p className="text-2xl font-bold text-slate-800">
                  ${Number(account.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>

              <div className="mt-4 text-xs text-slate-400">
                Created: {new Date(account.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create account modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4 animate-fadeIn">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-slate-800">Create New Account</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Account Type</label>
                <select
                  value={formData.account_type}
                  onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="savings">Savings Account</option>
                  <option value="checking">Checking Account</option>
                  <option value="fixed_deposit">Fixed Deposit</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Initial Deposit (USD)</label>
                <input
                  type="number"
                  value={formData.initial_deposit}
                  onChange={(e) => setFormData({ ...formData, initial_deposit: e.target.value })}
                  min="10"
                  step="0.01"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">Minimum deposit: $10</p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-3 border border-slate-300 text-slate-700 rounded-lg font-medium hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 py-3 bg-primary-800 hover:bg-primary-700 text-white rounded-lg font-medium btn-transition disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Accounts