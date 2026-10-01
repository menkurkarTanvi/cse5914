import { NavLink } from 'react-router-dom';
import './NavBar.css';

// This is the list of navigation links that will appear in the sidebar. Each link has a label and a path.
const navLinks = [
    { label: 'My Plan', path: '/my-plan' },
    { label: 'Progress', path: '/progress' },
    { label: 'AI Coach', path: '/ai-coach' },
    { label: 'Nutrition', path: '/nutrition' },
    { label: 'Profile', path: '/profile' },
];

export default function NavBar() {
    return (
        // Left sidebar with logo and navigation
        <aside className='sidebar'>
            <div className='sidebar-logo'>
                <h2>FitStack</h2>
                <p>AI Fitness Coach</p>
            </div>
            <nav className='sidebar-nav'>
                {navLinks.map((link) => (
                    // NavLink adds the "active" class automatically for the current route
                    <NavLink key={link.label} to={link.path} className='nav-link'>
                        {link.label}
                    </NavLink>
                ))}
            </nav>
        </aside>
    );
}