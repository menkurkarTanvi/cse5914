import type { Page } from '../types'

type Props = {
  page: Page
  setPage: (page: Page) => void
  logout: () => void
}

const navItems: { id: Page; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'plan', label: 'My Plan' },
  { id: 'progress', label: 'Progress' },
  { id: 'coach', label: 'AI Coach' },
  { id: 'nutrition', label: 'Nutrition' },
  { id: 'profile', label: 'Profile' },
]

function Sidebar({ page, setPage, logout }: Props) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-name">FitStack</div>
        <div className="brand-tagline">AI Fitness Coach</div>
      </div>

      <nav className="nav-list">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-button ${page === item.id ? 'active' : ''}`}
            onClick={() => setPage(item.id)}
          >
            {item.label}
          </button>
        ))}

        <button className="nav-button" onClick={logout}>
          Log Out
        </button>
      </nav>
    </aside>
  )
}

export default Sidebar