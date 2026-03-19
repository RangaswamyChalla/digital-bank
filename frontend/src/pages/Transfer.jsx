import { useState, useEffect } from 'react'
import api from '../services/api'

const Transfer = () => {
  const [accounts, setAccounts] = useState([])
  const [formData, setFormData] = useState({
    from_account_id: '',
    to_account_number: '',
    amount: '',
    transfer_type: 'internal',
    reference: '',
    description: ''
  })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showConfirmation, setShowConfirmation] = useState(false)

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await api.get('/api/accounts')
      setAccounts(response.data)
      if (response.data.length > 0) {
        setFormData(prev => ({ ...prev, from_account_id: response.data[0].id }))
      }
    } catch (error) {
      console.error('Failed to fetch accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const selectedAccount = accounts.find(a => a.id === formData.from_account_id)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (selectedAccount && parseFloat(formData.amount) > parseFloat(selectedAccount.balance)) {
      setError('Insufficient balance')
      return
    }

    setShowConfirmation(true)
  }

  const confirmTransfer = async () => {
    setSubmitting(true)
    setError('')

    try {
      await api.post('/api/transfers', {
        from_account_id: formData.from_account_id,
        to_account_number: formData.to_account_number,
        amount: parseFloat(formData.amount),
        transfer_type: formData.transfer_type,
        reference: formData.reference,
        description: formData.description
      })

      setSuccess(`Successfully transferred $${formData.amount} to account ${formData.to_account_number}`)
      setFormData({
        ...formData,
        to_account_number: '',
        amount: '',
        reference: '',
        description: ''
      })
      setShowConfirmation(false)
      fetchAccounts()
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed')
      setShowConfirmation(false)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-800"></div>
      </div>
    )
  }

  if (accounts.length === 0) {
    return (
      <div className="animate-fadeIn">
        <h1 className="text-2xl font-bold text-slate-800 mb-6">Transfer Money</h1>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-semibold text-slate-800 mb-2">No accounts available</h3>
          <p className="text-slate-500">Create an account first to transfer money</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Transfer Money</h1>
        <p className="text-slate-500">Send money to another account</p>
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

      {/* Transfer form */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">From Account</label>
            <select
              name="from_account_id"
              value={formData.from_account_id}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            >
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_number} - ${Number(account.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })} ({account.account_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">To Account Number</label>
            <input
              type="text"
              name="to_account_number"
              value={formData.to_account_number}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono"
              placeholder="Enter 10-digit account number"
              maxLength="10"
              minLength="10"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Amount (USD)</label>
            <input
              type="number"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="0.00"
              min="1"
              step="0.01"
              required
            />
            {selectedAccount && (
              <p className="text-xs text-slate-500 mt-1">
                Available: ${Number(selectedAccount.balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Transfer Type</label>
            <select
              name="transfer_type"
              value={formData.transfer_type}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="internal">Internal (Same Bank)</option>
              <option value="external">External (Other Bank)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Reference (Optional)</label>
            <input
              type="text"
              name="reference"
              value={formData.reference}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., Monthly rent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Note (Optional)</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Add a note..."
              rows="2"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-primary-800 hover:bg-primary-700 text-white rounded-lg font-medium btn-transition"
          >
            Continue to Confirmation
          </button>
        </form>
      </div>

      {/* Confirmation modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4 animate-fadeIn">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-800">Confirm Transfer</h2>
            </div>

            <div className="bg-slate-50 rounded-lg p-4 mb-6 space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-500">From:</span>
                <span className="font-mono text-slate-800">{accounts.find(a => a.id === formData.from_account_id)?.account_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">To:</span>
                <span className="font-mono text-slate-800">{formData.to_account_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Amount:</span>
                <span className="font-bold text-slate-800">${parseFloat(formData.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
              {formData.reference && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Reference:</span>
                  <span className="text-slate-800">{formData.reference}</span>
                </div>
              )}
            </div>

            <p className="text-sm text-slate-500 text-center mb-6">
              Please confirm the details above. This action cannot be undone.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirmation(false)}
                className="flex-1 py-3 border border-slate-300 text-slate-700 rounded-lg font-medium hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmTransfer}
                disabled={submitting}
                className="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium btn-transition disabled:opacity-50"
              >
                {submitting ? 'Processing...' : 'Confirm Transfer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Transfer