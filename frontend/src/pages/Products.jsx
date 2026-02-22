import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'

export default function Products() {
  const { user } = useAuth()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ sku: '', name: '', description: '', price: '', is_active: true })
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const fetchProducts = async () => {
    try {
      const res = await api.get(`/products/?search=${search}`)
      setProducts(res.data.results || res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProducts() }, [search])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/products/', form)
      setShowForm(false)
      setForm({ sku: '', name: '', description: '', price: '', is_active: true })
      fetchProducts()
    } catch (err) {
      setError(err.response?.data?.sku?.[0] || err.response?.data?.detail || 'Failed to create product')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this product?')) return
    try {
      await api.delete(`/products/${id}/`)
      fetchProducts()
    } catch (err) {
      alert(err.response?.data?.detail || 'Cannot delete — product may have existing orders')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Products</h1>
        {user?.isAdmin && (
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ New Product'}
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card mb-6">
          <h2 className="text-sm font-medium text-slate-400 mb-4">New Product</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-500 mb-1">SKU</label>
              <input className="input" placeholder="BP-001" value={form.sku}
                onChange={e => setForm({ ...form, sku: e.target.value })} required />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Name</label>
              <input className="input" placeholder="Brake Pad" value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Price (₹)</label>
              <input className="input" type="number" step="0.01" placeholder="500.00" value={form.price}
                onChange={e => setForm({ ...form, price: e.target.value })} required />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Description</label>
              <input className="input" placeholder="Optional" value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })} />
            </div>
            {error && <div className="col-span-2 text-red-400 text-sm">{error}</div>}
            <div className="col-span-2">
              <button type="submit" className="btn-primary">Create Product</button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="mb-4">
        <input className="input max-w-xs" placeholder="Search by name or SKU..."
          value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-500 text-left">
              <th className="px-6 py-3">SKU</th>
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">Price</th>
              <th className="px-6 py-3">Stock</th>
              <th className="px-6 py-3">Status</th>
              {user?.isAdmin && <th className="px-6 py-3">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-8 text-slate-500 text-center">Loading...</td></tr>
            ) : products.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-slate-500 text-center">No products found</td></tr>
            ) : products.map(p => (
              <tr key={p.id} className="hover:bg-slate-800/50">
                <td className="px-6 py-3 font-mono text-slate-400">{p.sku}</td>
                <td className="px-6 py-3 text-slate-200 font-medium">{p.name}</td>
                <td className="px-6 py-3 text-slate-300">₹{Number(p.price).toLocaleString('en-IN')}</td>
                <td className="px-6 py-3">
                  <span className={p.current_stock <= 10 ? 'text-red-400 font-mono' : 'text-slate-300 font-mono'}>
                    {p.current_stock}
                  </span>
                </td>
                <td className="px-6 py-3">
                  <span className={p.is_active ? 'text-emerald-400 text-xs' : 'text-slate-500 text-xs'}>
                    {p.is_active ? '● Active' : '○ Inactive'}
                  </span>
                </td>
                {user?.isAdmin && (
                  <td className="px-6 py-3">
                    <button onClick={() => handleDelete(p.id)}
                      className="text-slate-500 hover:text-red-400 text-xs transition-colors">
                      Delete
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}