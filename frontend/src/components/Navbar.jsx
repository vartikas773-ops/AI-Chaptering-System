const LINKS = [
  { key: 'home', label: 'Home' },
  { key: 'library', label: 'Library' },
  { key: 'settings', label: 'Settings' },
  { key: 'about', label: 'Help' },
]

export function Logo() {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="var(--ember)" />
      <rect x="7" y="9" width="18" height="3" rx="1.5" fill="#fff" />
      <rect x="7" y="15" width="12" height="3" rx="1.5" fill="#fff" />
      <rect x="7" y="21" width="15" height="3" rx="1.5" fill="#fff" />
    </svg>
  )
}

export default function Navbar({ theme, onSetTheme, page, onNavigate }) {
  return (
    <header className="navbar">
      <button className="brand" onClick={() => onNavigate('home')}>
        <Logo />
        <span>TopicTrail</span>
      </button>
      <nav className="nav-links" aria-label="Main">
        {LINKS.map((l) => (
          <button
            key={l.key}
            className={page === l.key ? 'nav-link active' : 'nav-link'}
            aria-current={page === l.key ? 'page' : undefined}
            onClick={() => onNavigate(l.key)}
          >
            {l.label}
          </button>
        ))}
      </nav>
      <button
        className="btn btn-ghost icon-btn"
        onClick={() => onSetTheme(theme === 'dark' ? 'light' : 'dark')}
        aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
      >
        {theme === 'dark' ? '☀' : '☾'}
      </button>
    </header>
  )
}
