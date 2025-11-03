import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts';
import { TrendingUp, DollarSign, Users, Activity } from 'lucide-react';
import api from '../../utils/api';

const AdminAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/admin/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
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

  const monthlyData = [
    { month: 'Jan', claims: 120, amount: 5200000, fraud: 15 },
    { month: 'Feb', claims: 150, amount: 6500000, fraud: 18 },
    { month: 'Mar', claims: 180, amount: 7800000, fraud: 22 },
    { month: 'Apr', claims: 165, amount: 7100000, fraud: 19 },
    { month: 'May', claims: 200, amount: 8900000, fraud: 25 },
    { month: 'Jun', claims: 190, amount: 8200000, fraud: 21 }
  ];

  const claimTypeData = [
    { type: 'Health', count: 450, avgAmount: 75000 },
    { type: 'Motor', count: 320, avgAmount: 120000 },
    { type: 'Property', count: 180, avgAmount: 350000 },
    { type: 'Life', count: 95, avgAmount: 500000 }
  ];

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">Analytics & Insights</span>
        </h1>
        <p className="text-gray-400">Comprehensive data analysis and trends</p>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { icon: TrendingUp, label: 'Avg Processing Time', value: '2.5 days', change: '-15%', color: 'blue' },
          { icon: DollarSign, label: 'Total Claims Value', value: '₹8.2Cr', change: '+12%', color: 'green' },
          { icon: Users, label: 'Active Users', value: '2,847', change: '+8%', color: 'purple' },
          { icon: Activity, label: 'Fraud Detection Rate', value: '95.2%', change: '+2%', color: 'red' }
        ].map((kpi, index) => {
          const Icon = kpi.icon;
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="glass p-6 rounded-xl"
            >
              <div className="flex items-center justify-between mb-3">
                <Icon className={`text-${kpi.color}-400`} size={24} />
                <span className="text-sm text-green-400">{kpi.change}</span>
              </div>
              <p className="text-sm text-gray-400 mb-1">{kpi.label}</p>
              <p className="text-2xl font-bold">{kpi.value}</p>
            </motion.div>
          );
        })}
      </div>

      {/* Claims Trend */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass p-6 rounded-xl"
      >
        <h3 className="text-xl font-bold mb-6">Claims Volume & Value Trend</h3>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={monthlyData}>
            <defs>
              <linearGradient id="colorClaims" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
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
            <Area type="monotone" dataKey="claims" stroke="#3b82f6" fillOpacity={1} fill="url(#colorClaims)" />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Claim Types Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="glass p-6 rounded-xl"
        >
          <h3 className="text-xl font-bold mb-6">Claims by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={claimTypeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="type" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="glass p-6 rounded-xl"
        >
          <h3 className="text-xl font-bold mb-6">Fraud Detection Trend</h3>
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
              <Line type="monotone" dataKey="fraud" stroke="#ef4444" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  );
};

export default AdminAnalytics;
