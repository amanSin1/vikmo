import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'

function StatusBadge({ status }) {
  return <span className={`badge-${status}`}>{status}</span>
}

export default function Orders() {
  const { user } = useAuth()
  const [orders, setOrders] = useState([])
  const [products, setProducts] = useState([])
  const [dealers, setDealers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // New order form state
  const [orderForm, setOrderForm] = useState({ dealer_id: '', notes: '', items: [{ product: '', quantity: 1 }] })

  const fetchOrders = async () => {
    try {
      const url = statusFilter ? `/orders/?status=${statusFilter}` : '/orders/'
      const res = await api.get(url)
      setOrders(res.data.results || res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const fetchProducts = async () => {
    const res = await api.get('/products/')
    setProducts(res.data.results || res.data)
  }

  const fetchDealers = async () => {
    if (!user?.isAdmin) return
    const res = await api.get('/dealers/')
    setDealers(res.data.results || res.data)
  }

  useEffect(() => { fetchOrders() }, [statusFilter])
  useEffect(() => { fetchProducts(); fetchDealers() }, [])

  const addItem = () => setOrderForm(f => ({ ...f, items: [...f.items, { product: '', quantity: 1 }] }))
  const removeItem = (i) => setOrderForm(f => ({ ...f, items: f.items.filter((_, idx) => idx !== i) }))
  const updateItem = (i, field, value) => setOrderForm(f => ({
    ...f,
    items: f.items.map((item, idx) => idx === i ? { ...item, [field]: value } : item)
  }))

  const handleCreateOrder = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const payload = {
        notes: orderForm.notes,
        items: orderForm.items.map(i => ({ product: parseInt(i.product), quantity: parseInt(i.quantity) })),
      }
      if (user?.isAdmin) payload.dealer_id = parseInt(orderForm.dealer_id)
      await api.post('/orders/', payload)
      setShowForm(false)
      setOrderForm({ dealer_id: '', notes: '', items: [{ product: '', quantity: 1 }] })
      setSuccess('Order created successfully')
      fetchOrders()
    } catch (err) {
      const data = err.response?.data
      setError(data?.items?.[0] || data?.error || data?.detail || 'Failed to create order')
    }
  }

  const handleConfirm = async (id) => {
    setError(''); setSuccess('')
    try {
      const res = await api.post(`/orders/${id}/confirm/`)
      setSuccess(res.data.message)
      fetchOrders()
    } catch (err) {
      const data = err.response?.data
      if (data?.stock_errors) {
        setError(`Stock error: ${data.stock_errors.map(e => e.error).join(', ')}`)
      } else {
        setError(data?.error || 'Failed to confirm order')
      }
    }
  }

  const handleDeliver = async (id) => {
    setError(''); setSuccess('')
    try {
      const res = await api.post(`/orders/${id}/deliver/`)
      setSuccess(res.data.message)
      fetchOrders()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to mark as delivered')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Orders</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Order'}
        </button>
      </div>

      {/* Notifications */}
      {success && (
        <div className="bg-emerald-900/30 border border-emerald-800 text-emerald-300 text-sm px-4 py-2 rounded-lg mb-4">
          {success}
        </div>
      )}
      {error && (
        <div className="bg-red-900/30 border border-red-800 text-red-300 text-sm px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Create Order Form */}
      {showForm && (
        <div className="card mb-6">
          <h2 className="text-sm font-medium text-slate-400 mb-4">New Draft Order</h2>
          <form onSubmit={handleCreateOrder} className="space-y-4">
            {user?.isAdmin && (
              <div>
                <label className="block text-xs text-slate-500 mb-1">Dealer</label>
                <select className="input" value={orderForm.dealer_id}
                  onChange={e => setOrderForm({ ...orderForm, dealer_id: e.target.value })} required>
                  <option value="">Select dealer...</option>
                  {dealers.map(d => (
                    <option key={d.id} value={d.id}>{d.name} ({d.dealer_code})</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-xs text-slate-500 mb-1">Notes (optional)</label>
              <input className="input" placeholder="Urgent, handle with care..."
                value={orderForm.notes} onChange={e => setOrderForm({ ...orderForm, notes: e.target.value })} />
            </div>

            {/* Items */}
            <div>
              <label className="block text-xs text-slate-500 mb-2">Order Items</label>
              <div className="space-y-2">
                {orderForm.items.map((item, i) => (
                  <div key={i} className="flex gap-3 items-center">
                    <select className="input flex-1" value={item.product}
                      onChange={e => updateItem(i, 'product', e.target.value)} required>
                      <option value="">Select product...</option>
                      {products.filter(p => p.is_active).map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name} — ₹{p.price} (Stock: {p.current_stock})
                        </option>
                      ))}
                    </select>
                    <input className="input w-24" type="number" min="1" placeholder="Qty"
                      value={item.quantity} onChange={e => updateItem(i, 'quantity', e.target.value)} required />
                    {orderForm.items.length > 1 && (
                      <button type="button" onClick={() => removeItem(i)}
                        className="text-slate-500 hover:text-red-400 transition-colors">✕</button>
                    )}
                  </div>
                ))}
              </div>
              <button type="button" onClick={addItem}
                className="mt-2 text-brand-400 hover:text-brand-300 text-sm transition-colors">
                + Add item
              </button>
            </div>

            <button type="submit" className="btn-primary">Create Draft Order</button>
          </form>
        </div>
      )}

      {/* Status filter */}
      <div className="flex gap-2 mb-4">
        {['', 'draft', 'confirmed', 'delivered'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              statusFilter === s ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
            }`}>
            {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Orders table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-500 text-left">
              <th className="px-6 py-3">Order #</th>
              {user?.isAdmin && <th className="px-6 py-3">Dealer</th>}
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Items</th>
              <th className="px-6 py-3 text-right">Total</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-8 text-slate-500 text-center">Loading...</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-slate-500 text-center">No orders found</td></tr>
            ) : orders.map(order => (
              <>
                <tr key={order.id} className="hover:bg-slate-800/50 cursor-pointer"
                  onClick={() => setExpanded(expanded === order.id ? null : order.id)}>
                  <td className="px-6 py-3 font-mono text-slate-300">{order.order_number}</td>
                  {user?.isAdmin && <td className="px-6 py-3 text-slate-400">{order.dealer_name}</td>}
                  <td className="px-6 py-3"><StatusBadge status={order.status} /></td>
                  <td className="px-6 py-3 text-slate-400">{order.item_count} item(s)</td>
                  <td className="px-6 py-3 text-right text-slate-200 font-mono">
                    ₹{Number(order.total_amount).toLocaleString('en-IN')}
                  </td>
                  <td className="px-6 py-3" onClick={e => e.stopPropagation()}>
                    <div className="flex gap-2">
                      {order.status === 'draft' && (
                        <button onClick={() => handleConfirm(order.id)} className="btn-primary text-xs px-2 py-1">
                          Confirm
                        </button>
                      )}
                      {order.status === 'confirmed' && (
                        <button onClick={() => handleDeliver(order.id)} className="btn-success text-xs px-2 py-1">
                          Deliver
                        </button>
                      )}
                      {order.status === 'delivered' && (
                        <span className="text-emerald-500 text-xs">✓ Complete</span>
                      )}
                    </div>
                  </td>
                </tr>

                {/* Expanded order items */}
                {expanded === order.id && (
                  <tr key={`exp-${order.id}`} className="bg-slate-800/20">
                    <td colSpan={user?.isAdmin ? 6 : 5} className="px-6 py-4">
                      <div className="text-xs text-slate-500 mb-2">Order Items</div>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-slate-500 text-left border-b border-slate-800">
                            <th className="pb-1">Product</th>
                            <th className="pb-1">SKU</th>
                            <th className="pb-1 text-right">Qty</th>
                            <th className="pb-1 text-right">Unit Price</th>
                            <th className="pb-1 text-right">Line Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {order.items?.map(item => (
                            <tr key={item.id}>
                              <td className="py-1 text-slate-200">{item.product_name}</td>
                              <td className="py-1 text-slate-500 font-mono">{item.product_sku}</td>
                              <td className="py-1 text-right text-slate-300">{item.quantity}</td>
                              <td className="py-1 text-right text-slate-300">₹{Number(item.unit_price).toLocaleString('en-IN')}</td>
                              <td className="py-1 text-right text-slate-200 font-medium">₹{Number(item.line_total).toLocaleString('en-IN')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {order.notes && (
                        <p className="text-slate-500 text-xs mt-3">Notes: {order.notes}</p>
                      )}
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