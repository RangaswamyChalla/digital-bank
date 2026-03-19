/**
 * Analytics Service
 * Fetches dashboard analytics and fraud data
 */

import api from './api'

export const analyticsService = {
  // Get transaction summary
  async getTransactionsSummary(days = 30) {
    try {
      const response = await api.get(`/api/analytics/transactions-summary?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch transactions summary:', error)
      throw error
    }
  },

  // Get daily transaction data
  async getDailyTransactions(days = 30) {
    try {
      const response = await api.get(`/api/analytics/daily-transactions?days=${days}`)
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch daily transactions:', error)
      throw error
    }
  },

  // Get user growth metrics
  async getUserGrowth(days = 30) {
    try {
      const response = await api.get(`/api/analytics/user-growth?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch user growth:', error)
      throw error
    }
  },

  // Get fraud metrics
  async getFraudMetrics(days = 30) {
    try {
      const response = await api.get(`/api/analytics/fraud-metrics?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch fraud metrics:', error)
      throw error
    }
  },

  // Get complete dashboard stats
  async getDashboardStats() {
    try {
      const response = await api.get('/analytics/dashboard-stats')
      return response.data
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error)
      throw error
    }
  },

  // Fraud Detection APIs
  async getFraudAlerts(limit = 50, offset = 0, status = null) {
    try {
      let url = `/api/fraud/alerts?limit=${limit}&offset=${offset}`
      if (status) url += `&status_filter=${status}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Failed to fetch fraud alerts:', error)
      throw error
    }
  },

  async getFraudAlertDetails(alertId) {
    try {
      const response = await api.get(`/api/fraud/alerts/${alertId}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch alert details:', error)
      throw error
    }
  },

  async takeAlertAction(alertId, action, notes = '') {
    try {
      const response = await api.post(`/api/fraud/alerts/${alertId}/action`, {
        action,
        notes
      })
      return response.data
    } catch (error) {
      console.error('Failed to take alert action:', error)
      throw error
    }
  },

  async getUserRiskProfile(userId) {
    try {
      const response = await api.get(`/api/fraud/user-risk/${userId}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch user risk profile:', error)
      throw error
    }
  },

  async getFraudStatistics() {
    try {
      const response = await api.get('/fraud/statistics')
      return response.data
    } catch (error) {
      console.error('Failed to fetch fraud statistics:', error)
      throw error
    }
  }
}

export default analyticsService
