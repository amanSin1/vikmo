import { useEffect, useState } from 'react'
import api from '../api/axios'

export default function Dealers() {
  const [dealers, setDealers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ username: '', email: '', password: '', name: '', phone: '', address: '', city: '', state: '', pincode: '' })
  const [error, setError] = useState('')

  const fetchDealers = async () => {
    try {
      const res = await api.get('/dealers/')
      setDealers(res.data.results || res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchDealers() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/dealers/', form)
      setShowForm(false)
      setForm({ username: '', email: '', password: '', name: '', phone: '', address: '', city: '', state: '', pincode: '' })
      fetchDealers()
    } catch (err) {
      const data = err.response?.data
      setError(data?.username?.[0] || data?.email?.[0] || data?.detail || 'Failed to create dealer')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Dealers</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Dealer'}
        </button>
      </div>

      {showForm && (
        <div className="card mb-6">
          <h2 className="text-sm font-medium text-slate-400 mb-4">Create Dealer Account</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
            {[
              { key: 'username', label: 'Username', placeholder: 'abcmotors' },
              { key: 'email', label: 'Email', placeholder: 'abc@motors.com', type: 'email' },
              { key: 'password', label: 'Password', placeholder: '••••••••', type: 'password' },
              { key: 'name', label: 'Business Name', placeholder: 'ABC Motors' },
              { key: 'phone', label: 'Phone', placeholder: '9876543210' },
              { key: 'city', label: 'City', placeholder: 'Mumbai' },
              { key: 'state', label: 'State', placeholder: 'Maharashtra' },
              { key: 'pincode', label: 'Pincode', placeholder: '400001' },
            ].map(field => (
              <div key={field.key}>
                <label className="block text-xs text-slate-500 mb-1">{field.label}</label>
                <input className="input" type={field.type || 'text'} placeholder={field.placeholder}
                  value={form[field.key]} onChange={e => setForm({ ...form, [field.key]: e.target.value })} required />
              </div>
            ))}
            <div className="col-span-2">
              <label className="block text-xs text-slate-500 mb-1">Address</label>
              <input className="input" placeholder="123 Main Street" value={form.address}
                onChange={e => setForm({ ...form, address: e.target.value })} required />
            </div>
            {error && <div className="col-span-2 text-red-400 text-sm">{error}</div>}
            <div className="col-span-2">
              <button type="submit" className="btn-primary">Create Dealer</button>
            </div>
          </form>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-500 text-left">
              <th className="px-6 py-3">Dealer Code</th>
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">Username</th>
              <th className="px-6 py-3">Email</th>
              <th className="px-6 py-3">City</th>
              <th className="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-8 text-slate-500 text-center">Loading...</td></tr>
            ) : dealers.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-slate-500 text-center">No dealers yet</td></tr>
            ) : dealers.map(d => (
              <tr key={d.id} className="hover:bg-slate-800/50">
                <td className="px-6 py-3 font-mono text-brand-400">{d.dealer_code}</td>
                <td className="px-6 py-3 text-slate-200 font-medium">{d.name}</td>
                <td className="px-6 py-3 text-slate-400">{d.username}</td>
                <td className="px-6 py-3 text-slate-400">{d.email}</td>
                <td className="px-6 py-3 text-slate-400">{d.city}</td>
                <td className="px-6 py-3">
                  <span className={d.is_active ? 'text-emerald-400 text-xs' : 'text-slate-500 text-xs'}>
                    {d.is_active ? '● Active' : '○ Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}