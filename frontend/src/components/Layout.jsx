import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const adminLinks = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/products', label: 'Products', icon: '⬡' },
  { to: '/inventory', label: 'Inventory', icon: '◈' },
  { to: '/dealers', label: 'Dealers', icon: '◉' },
  { to: '/orders', label: 'Orders', icon: '◎' },
]

const dealerLinks = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/products', label: 'Browse Products', icon: '⬡' },
  { to: '/orders', label: 'My Orders', icon: '◎' },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const links = user?.isAdmin ? adminLinks : dealerLinks

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-slate-800">
          <span className="font-mono text-brand-500 font-bold text-lg tracking-tight">VIKMO</span>
          <p className="text-slate-500 text-xs mt-0.5">
            {user?.isAdmin ? 'Admin Portal' : 'Dealer Portal'}
          </p>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
                }`
              }
            >
              <span className="text-base">{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* User info + logout */}
        <div className="px-3 py-4 border-t border-slate-800">
          <div className="px-3 py-2 mb-2">
            <p className="text-slate-300 text-sm font-medium truncate">{user?.username}</p>
            <p className="text-slate-500 text-xs">{user?.isAdmin ? 'Administrator' : 'Dealer'}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg text-sm transition-colors"
          >
            Sign out →
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-slate-950">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}