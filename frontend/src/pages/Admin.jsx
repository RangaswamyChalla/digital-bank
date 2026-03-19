import { useState, useEffect } from 'react'
import api from '../services/api'

const Admin = () => {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [kycApplications, setKycApplications] = useState([])
  const [activeTab, setActiveTab] = useState('stats')
  const [loading, setLoading] = useState(true)
  const [reviewing, setReviewing] = useState(false)
  const [selectedKyc, setSelectedKyc] = useState(null)

  useEffect(() => {
    fetchData()
  }, [activeTab])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'stats') {
        const response = await api.get('/api/admin/stats')
        setStats(response.data)
      } else if (activeTab === 'users') {
        const response = await api.get('/api/admin/users?limit=100')
        setUsers(response.data)
      } else if (activeTab === 'kyc') {
        const response = await api.get('/api/kyc/admin/list')
        setKycApplications(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleKycReview = async (approved, reason = '') => {
    if (!selectedKyc) return
    setReviewing(true)

    try {
      await api.put(`/api/kyc/admin/review/${selectedKyc.id}`, {
        approved,
        reason
      })
      await fetchData()
      setSelectedKyc(null)
    } catch (error) {
      console.error('Failed to review KYC:', error)
    } finally {
      setReviewing(false)
    }
  }

  const handleLockUser = async (userId, locked) => {
    try {
      await api.put(`/api/admin/users/${userId}/lock`, { locked })
      await fetchData()
    } catch (error) {
      console.error('Failed to lock user:', error)
    }
  }

  const getKycStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      submitted: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    }
    return styles[status] || 'bg-slate-100 text-slate-800'
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Admin Dashboard</h1>
        <p className="text-slate-500">Manage users and applications</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        {['stats', 'users', 'kyc'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize transition-colors ${
              activeTab === tab
                ? 'text-primary-800 border-b-2 border-primary-800'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab === 'kyc' ? 'KYC Applications' : tab}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-800"></div>
        </div>
      ) : (
        <>
          {/* Stats */}
          {activeTab === 'stats' && stats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-3xl font-bold text-slate-800 mt-1">{stats.total_users}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <p className="text-sm text-slate-500">Total Accounts</p>
                <p className="text-3xl font-bold text-slate-800 mt-1">{stats.total_accounts}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <p className="text-sm text-slate-500">Total Transactions</p>
                <p className="text-3xl font-bold text-slate-800 mt-1">{stats.total_transactions}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <p className="text-sm text-slate-500">Pending KYC</p>
                <p className="text-3xl font-bold text-yellow-600 mt-1">{stats.pending_kyc}</p>
              </div>
            </div>
          )}

          {/* Users */}
          {activeTab === 'users' && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">User</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">KYC Level</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-slate-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 font-medium">
                              {user.full_name.charAt(0)}
                            </div>
                            <span className="font-medium text-slate-800">{user.full_name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-slate-600">{user.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                            Level {user.kyc_level}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getKycStatusBadge(user.kyc_status)}`}>
                            {user.kyc_status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => handleLockUser(user.id, !user.is_active)}
                            className={`px-3 py-1 rounded text-xs font-medium ${
                              user.is_active
                                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                : 'bg-green-100 text-green-700 hover:bg-green-200'
                            }`}
                          >
                            {user.is_active ? 'Lock' : 'Unlock'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* KYC Applications */}
          {activeTab === 'kyc' && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              {kycApplications.length === 0 ? (
                <div className="p-12 text-center">
                  <p className="text-slate-500">No pending KYC applications</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">User</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Document Type</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Doc Number</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Submitted</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {kycApplications.map((app) => (
                        <tr key={app.id} className="hover:bg-slate-50">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-800 font-medium">
                                {app.full_name.charAt(0)}
                              </div>
                              <div>
                                <p className="font-medium text-slate-800">{app.full_name}</p>
                                <p className="text-sm text-slate-500">{app.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-slate-600 capitalize">{app.kyc_document_type?.replace('_', ' ')}</td>
                          <td className="px-6 py-4 font-mono text-slate-600">****{app.kyc_document_number?.slice(-4)}</td>
                          <td className="px-6 py-4 text-slate-600">
                            {app.kyc_submitted_at ? new Date(app.kyc_submitted_at).toLocaleDateString() : '-'}
                          </td>
                          <td className="px-6 py-4">
                            {selectedKyc?.id === app.id ? (
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleKycReview(true)}
                                  disabled={reviewing}
                                  className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() => handleKycReview(false, 'Documents not verified')}
                                  disabled={reviewing}
                                  className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
                                >
                                  Reject
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => setSelectedKyc(app)}
                                className="px-3 py-1 bg-primary-800 text-white rounded text-xs hover:bg-primary-700"
                              >
                                Review
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Admin