import { useState, useCallback } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useRecommendations() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const fetch = useCallback(async ({ amount, durationValue, durationUnit, magicMode, riskAppetite }) => {
    setLoading(true)
    setError(null)
    setData(null)

    try {
      const resp = await axios.post(`${API_BASE}/api/recommend`, {
        amount,
        duration_value: durationValue,
        duration_unit:  durationUnit,
        magic_mode:     magicMode,
        risk_appetite:  riskAppetite,
      }, { timeout: 60000 })

      setData(resp.data)
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Analysis failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return { data, loading, error, fetch, reset }
}
