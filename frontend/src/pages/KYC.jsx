import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

const KYC = () => {
  const { user, refreshUser } = useAuth()
  const [kycStatus, setKycStatus] = useState(null)
  const [formData, setFormData] = useState({
    document_type: 'national_id',
    document_number: '',
    document_file: '',
    address: ''
  })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    fetchKycStatus()
  }, [])

  const fetchKycStatus = async () => {
    try {
      const response = await api.get('/kyc/status')
      setKycStatus(response.data)
    } catch (error) {
      console.error('Failed to fetch KYC status:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)

    try {
      await api.post('/kyc/submit', formData)
      setSuccess('KYC application submitted successfully!')
      await refreshUser()
      await fetchKycStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit KYC application')
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      submitted: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    }
    return styles[status] || 'bg-slate-100 text-slate-800'
  }

  const getLevelBadge = (level) => {
    const styles = {
      0: 'bg-slate-200 text-slate-700',
      1: 'bg-blue-100 text-blue-700',
      2: 'bg-green-100 text-green-700',
      3: 'bg-purple-100 text-purple-700'
    }
    return styles[level] || styles[0]
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
      <div>
        <h1 className="text-2xl font-bold text-slate-800">KYC Verification</h1>
        <p className="text-slate-500">Verify your identity to unlock full banking features</p>
      </div>

      {/* KYC Status Card */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">Current Status</p>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-2xl font-bold text-slate-800 capitalize">{kycStatus?.kyc_status || 'pending'}</p>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(kycStatus?.kyc_status)}`}>
                {kycStatus?.kyc_status?.toUpperCase() || 'PENDING'}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-500">Verification Level</p>
            <div className="flex items-center gap-2 mt-1 justify-end">
              <span className="text-2xl font-bold text-slate-800">{kycStatus?.kyc_level || 0}</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLevelBadge(kycStatus?.kyc_level)}`}>
                Level {kycStatus?.kyc_level || 0}
              </span>
            </div>
          </div>
        </div>

        {kycStatus?.kyc_status === 'rejected' && kycStatus?.kyc_rejection_reason && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm font-medium text-red-800">Rejection Reason:</p>
            <p className="text-sm text-red-600">{kycStatus.kyc_rejection_reason}</p>
          </div>
        )}

        {kycStatus?.kyc_status === 'submitted' && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">Your application is being reviewed. This usually takes 1-2 business days.</p>
          </div>
        )}
      </div>

      {/* Benefits of KYC */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className={`p-4 rounded-xl border ${kycStatus?.kyc_level >= 1 ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 mb-2">
            {kycStatus?.kyc_level >= 1 ? (
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : (
              <div className="w-5 h-5 rounded-full border-2 border-slate-300"></div>
            )}
            <span className="font-medium text-slate-800">Level 1: Email Verified</span>
          </div>
          <p className="text-sm text-slate-500">Basic account access</p>
        </div>

        <div className={`p-4 rounded-xl border ${kycStatus?.kyc_level >= 2 ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 mb-2">
            {kycStatus?.kyc_level >= 2 ? (
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : (
              <div className="w-5 h-5 rounded-full border-2 border-slate-300"></div>
            )}
            <span className="font-medium text-slate-800">Level 2: ID Verified</span>
          </div>
          <p className="text-sm text-slate-500">Create accounts & transfer money</p>
        </div>

        <div className={`p-4 rounded-xl border ${kycStatus?.kyc_level >= 3 ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 mb-2">
            {kycStatus?.kyc_level >= 3 ? (
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : (
              <div className="w-5 h-5 rounded-full border-2 border-slate-300"></div>
            )}
            <span className="font-medium text-slate-800">Level 3: Full Verified</span>
          </div>
          <p className="text-sm text-slate-500">Higher limits & all features</p>
        </div>
      </div>

      {/* KYC Form */}
      {kycStatus?.kyc_status !== 'approved' && kycStatus?.kyc_status !== 'submitted' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-6">Submit KYC Documents</h2>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-600">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Document Type</label>
              <select
                name="document_type"
                value={formData.document_type}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              >
                <option value="national_id">National ID</option>
                <option value="passport">Passport</option>
                <option value="driver_license">Driver's License</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Document Number</label>
              <input
                type="text"
                name="document_number"
                value={formData.document_number}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono"
                placeholder="Enter document number"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Address</label>
              <textarea
                name="address"
                value={formData.address}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Enter your full address"
                rows="3"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Document Upload (Simulated)</label>
              <input
                type="text"
                name="document_file"
                value={formData.document_file}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Enter filename (simulated)"
              />
              <p className="text-xs text-slate-500 mt-1">For demo purposes, enter any filename</p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-primary-800 hover:bg-primary-700 text-white rounded-lg font-medium btn-transition disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit KYC Application'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default KYC