import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Users, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Activity,
  BarChart3
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import api from '../../utils/api';
import { formatCurrency } from '../../utils/helpers';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/admin/dashboard');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const statCards = [
    {
      icon: FileText,
      label: 'Total Claims',
      value: stats?.total_claims || 0,
      change: '+12.5%',
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-500/20'
    },
    {
      icon: Clock,
      label: 'Pending Review',
      value: stats?.pending_claims || 0,
      change: '-5.2%',
      color: 'from-yellow-500 to-orange-500',
      bgColor: 'bg-yellow-500/20'
    },
    {
      icon: AlertTriangle,
      label: 'High Risk',
      value: stats?.high_risk_claims || 0,
      change: '+8.1%',
      color: 'from-red-500 to-pink-500',
      bgColor: 'bg-red-500/20'
    },
    {
      icon: TrendingUp,
      label: 'Approval Rate',
      value: stats?.approval_rate ? `${stats.approval_rate}%` : '0%',
      change: '+3.4%',
      color: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-500/20'
    }
  ];

  const claimTypeData = [
    { name: 'Health', value: 45, color: '#3b82f6' },
    { name: 'Motor', value: 25, color: '#8b5cf6' },
    { name: 'Property', value: 20, color: '#ec4899' },
    { name: 'Life', value: 10, color: '#f59e0b' }
  ];

  const monthlyData = [
    { month: 'Jan', claims: 120, approved: 95 },
    { month: 'Feb', claims: 150, approved: 120 },
    { month: 'Mar', claims: 180, approved: 145 },
    { month: 'Apr', claims: 165, approved: 135 },
    { month: 'May', claims: 200, approved: 165 },
    { month: 'Jun', claims: 190, approved: 155 }
  ];

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">Admin Dashboard</span>
        </h1>
        <p className="text-gray-400">Monitor and manage all claims in real-time</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.1 }}
              className="glass p-6 rounded-xl card-hover"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon size={24} className="text-white" />
                </div>
                <span className="text-sm text-green-400">{stat.change}</span>
              </div>
              <p className="text-gray-400 text-sm mb-1">{stat.label}</p>
              <p className="text-3xl font-bold gradient-text">{stat.value}</p>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Claims by Type */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="glass p-6 rounded-xl"
        >
          <h3 className="text-xl font-bold mb-6">Claims by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={claimTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {claimTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Monthly Trends */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="glass p-6 rounded-xl"
        >
          <h3 className="text-xl font-bold mb-6">Monthly Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '8px'
                }}
              />
              <Line type="monotone" dataKey="claims" stroke="#3b82f6" strokeWidth={2} />
              <Line type="monotone" dataKey="approved" stroke="#10b981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        <Link to="/admin/claims?status=pending" className="glass p-6 rounded-xl hover:bg-white/10 transition-all group">
          <Clock className="text-yellow-400 mb-4 group-hover:scale-110 transition-transform" size={32} />
          <h3 className="text-lg font-bold mb-2">Review Pending</h3>
          <p className="text-gray-400 text-sm">Process waiting claims</p>
        </Link>

        <Link to="/admin/claims?risk=high" className="glass p-6 rounded-xl hover:bg-white/10 transition-all group">
          <AlertTriangle className="text-red-400 mb-4 group-hover:scale-110 transition-transform" size={32} />
          <h3 className="text-lg font-bold mb-2">High Risk Claims</h3>
          <p className="text-gray-400 text-sm">Review fraud alerts</p>
        </Link>

        <Link to="/admin/analytics" className="glass p-6 rounded-xl hover:bg-white/10 transition-all group">
          <BarChart3 className="text-blue-400 mb-4 group-hover:scale-110 transition-transform" size={32} />
          <h3 className="text-lg font-bold mb-2">View Analytics</h3>
          <p className="text-gray-400 text-sm">Detailed insights</p>
        </Link>
      </motion.div>
    </div>
  );
};

export default AdminDashboard;
