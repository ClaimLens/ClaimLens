import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  FileText, 
  PlusCircle, 
  User, 
  LogOut,
  BarChart3,
  Shield,
  Menu,
  X
} from 'lucide-react';
import { useState } from 'react';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const customerMenuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: PlusCircle, label: 'File Claim', path: '/dashboard/file-claim' },
    { icon: FileText, label: 'My Claims', path: '/dashboard/my-claims' },
    { icon: User, label: 'Profile', path: '/dashboard/profile' },
  ];

  const adminMenuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/admin' },
    { icon: FileText, label: 'All Claims', path: '/admin/claims' },
    { icon: BarChart3, label: 'Analytics', path: '/admin/analytics' },
  ];

  const menuItems = user?.role === 'admin' ? adminMenuItems : customerMenuItems;

  return (
    <div className="min-h-screen flex">
      {/* Mobile menu button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 glass p-2 rounded-lg"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 glass border-r border-white/10
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-full flex flex-col p-6">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <Shield className="text-primary-400" size={32} />
            <div>
              <h1 className="text-xl font-bold gradient-text">ClaimLens</h1>
              <p className="text-xs text-gray-400">AI-Powered Claims</p>
            </div>
          </div>

          {/* User Info */}
          <div className="glass-dark p-4 rounded-lg mb-6">
            <p className="text-sm text-gray-400">Welcome back,</p>
            <p className="font-semibold">{user?.full_name}</p>
            <p className="text-xs text-primary-400 mt-1 uppercase">{user?.role}</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg
                    transition-all duration-300
                    ${isActive 
                      ? 'bg-primary-600/30 text-primary-300 shadow-lg shadow-primary-500/20' 
                      : 'hover:bg-white/5 text-gray-300 hover:text-white'
                    }
                  `}
                >
                  <Icon size={20} />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg
                     hover:bg-red-500/20 text-gray-300 hover:text-red-300
                     transition-all duration-300 w-full"
          >
            <LogOut size={20} />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-4 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default DashboardLayout;
