import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'

function StatCard({ label, value, sub }) {
  return (
    <div className="card">
      <p className="text-slate-500 text-sm">{label}</p>
      <p className="text-3xl font-bold text-slate-100 mt-1">{value ?? '—'}</p>
      {sub && <p className="text-slate-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [summary, setSummary] = useState(null)
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (user?.isAdmin) {
          const res = await api.get('/orders/summary/')
          setSummary(res.data)
        } else {
          const res = await api.get('/orders/')
          setOrders(res.data.results || res.data)
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [user])

  if (loading) return <div className="text-slate-500">Loading...</div>

  if (user?.isAdmin && summary) {
    const byStatus = summary.orders_by_status || {}
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-6">Dashboard</h1>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Orders" value={summary.total_orders} />
          <StatCard label="Draft" value={byStatus.draft || 0} />
          <StatCard label="Confirmed" value={byStatus.confirmed || 0} />
          <StatCard label="Delivered" value={byStatus.delivered || 0} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Revenue */}
          <div className="card">
            <h2 className="text-sm font-medium text-slate-400 mb-3">Total Revenue</h2>
            <p className="text-3xl font-bold text-emerald-400">
              ₹{Number(summary.total_confirmed_revenue).toLocaleString('en-IN')}
            </p>
            <p className="text-slate-500 text-xs mt-1">From confirmed + delivered orders</p>
          </div>

          {/* Low stock alert */}
          <div className="card">
            <h2 className="text-sm font-medium text-slate-400 mb-3">
              Low Stock Alert
              {summary.low_stock_alert?.length > 0 && (
                <span className="ml-2 bg-red-900 text-red-300 text-xs px-1.5 py-0.5 rounded-full">
                  {summary.low_stock_alert.length}
                </span>
              )}
            </h2>
            {summary.low_stock_alert?.length === 0 ? (
              <p className="text-emerald-400 text-sm">All products well stocked ✓</p>
            ) : (
              <div className="space-y-2">
                {summary.low_stock_alert.map((item, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-slate-300">{item.product__name}</span>
                    <span className="text-red-400 font-mono">{item.quantity} left</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top products */}
          <div className="card lg:col-span-2">
            <h2 className="text-sm font-medium text-slate-400 mb-3">Top Products by Volume</h2>
            {summary.top_5_products_by_quantity?.length === 0 ? (
              <p className="text-slate-500 text-sm">No confirmed orders yet</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-left border-b border-slate-800">
                    <th className="pb-2">Product</th>
                    <th className="pb-2">SKU</th>
                    <th className="pb-2 text-right">Units Sold</th>
                    <th className="pb-2 text-right">Revenue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {summary.top_5_products_by_quantity.map((p, i) => (
                    <tr key={i}>
                      <td className="py-2 text-slate-200">{p.product__name}</td>
                      <td className="py-2 text-slate-500 font-mono">{p.product__sku}</td>
                      <td className="py-2 text-right text-slate-200">{p.total_quantity}</td>
                      <td className="py-2 text-right text-emerald-400">₹{Number(p.total_revenue).toLocaleString('en-IN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Dealer dashboard
  const draft = orders.filter(o => o.status === 'draft').length
  const confirmed = orders.filter(o => o.status === 'confirmed').length
  const delivered = orders.filter(o => o.status === 'delivered').length

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-100 mb-6">My Dashboard</h1>
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Draft Orders" value={draft} />
        <StatCard label="Confirmed" value={confirmed} />
        <StatCard label="Delivered" value={delivered} />
      </div>
      <div className="card">
        <h2 className="text-sm font-medium text-slate-400 mb-3">Recent Orders</h2>
        {orders.length === 0 ? (
          <p className="text-slate-500 text-sm">No orders yet. Place your first order!</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 text-left border-b border-slate-800">
                <th className="pb-2">Order #</th>
                <th className="pb-2">Status</th>
                <th className="pb-2 text-right">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {orders.slice(0, 5).map(o => (
                <tr key={o.id}>
                  <td className="py-2 font-mono text-slate-300">{o.order_number}</td>
                  <td className="py-2">
                    <span className={`badge-${o.status}`}>{o.status}</span>
                  </td>
                  <td className="py-2 text-right text-slate-200">₹{Number(o.total_amount).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}