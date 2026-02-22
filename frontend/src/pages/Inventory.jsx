import { useEffect, useState } from 'react'
import api from '../api/axios'

export default function Inventory() {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const [adjusting, setAdjusting] = useState(null) // product_id being adjusted
  const [form, setForm] = useState({ quantity: '', reason: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const fetchInventory = async () => {
    try {
      const res = await api.get('/inventory/')
      setInventory(res.data.results || res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchInventory() }, [])

  const handleAdjust = async (productId) => {
    setError('')
    setSuccess('')
    try {
      const res = await api.put(`/inventory/${productId}/adjust/`, {
        quantity: parseInt(form.quantity),
        reason: form.reason || 'Manual adjustment by admin',
      })
      setSuccess(res.data.message)
      setAdjusting(null)
      setForm({ quantity: '', reason: '' })
      fetchInventory()
    } catch (err) {
      setError(err.response?.data?.quantity?.[0] || 'Failed to update stock')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Inventory</h1>
        <span className="text-slate-500 text-sm">Admin only — manual stock corrections</span>
      </div>

      {success && (
        <div className="bg-emerald-900/30 border border-emerald-800 text-emerald-300 text-sm px-4 py-2 rounded-lg mb-4">
          {success}
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-500 text-left">
              <th className="px-6 py-3">Product</th>
              <th className="px-6 py-3">SKU</th>
              <th className="px-6 py-3">Current Stock</th>
              <th className="px-6 py-3">Last Updated</th>
              <th className="px-6 py-3">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-8 text-slate-500 text-center">Loading...</td></tr>
            ) : inventory.map(item => (
              <>
                <tr key={item.id} className="hover:bg-slate-800/50">
                  <td className="px-6 py-3 text-slate-200 font-medium">{item.product_name}</td>
                  <td className="px-6 py-3 font-mono text-slate-400">{item.product_sku}</td>
                  <td className="px-6 py-3">
                    <span className={`font-mono font-bold ${item.quantity <= 10 ? 'text-red-400' : item.quantity <= 50 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                      {item.quantity}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-slate-500 text-xs">
                    {new Date(item.updated_at).toLocaleString('en-IN')}
                  </td>
                  <td className="px-6 py-3">
                    <button
                      onClick={() => setAdjusting(adjusting === item.product ? null : item.product)}
                      className="text-brand-400 hover:text-brand-300 text-xs transition-colors"
                    >
                      Adjust Stock
                    </button>
                  </td>
                </tr>
                {adjusting === item.product && (
                  <tr key={`adj-${item.id}`} className="bg-slate-800/30">
                    <td colSpan={5} className="px-6 py-4">
                      <div className="flex items-end gap-3">
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">New Quantity</label>
                          <input className="input w-32" type="number" min="0" placeholder="0"
                            value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} />
                        </div>
                        <div className="flex-1">
                          <label className="block text-xs text-slate-500 mb-1">Reason</label>
                          <input className="input" placeholder="e.g. Initial stock load, Stock correction..."
                            value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })} />
                        </div>
                        <button className="btn-primary" onClick={() => handleAdjust(item.product)}>
                          Update
                        </button>
                        <button className="btn-secondary" onClick={() => setAdjusting(null)}>
                          Cancel
                        </button>
                      </div>
                      {error && <p className="text-red-400 text-xs mt-2">{error}</p>}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}