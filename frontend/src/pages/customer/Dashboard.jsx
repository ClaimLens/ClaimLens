import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  XCircle,
  FileText,
  ArrowRight,
  AlertTriangle,
  Activity
} from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate, getStatusColor } from '../../utils/helpers';

const CustomerDashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentClaims, setRecentClaims] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, claimsRes] = await Promise.all([
        api.get('/claims/statistics'),
        api.get('/claims/user?limit=5')
      ]);
      
      setStats(statsRes.data);
      setRecentClaims(claimsRes.data);
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
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-500/20'
    },
    {
      icon: Clock,
      label: 'Pending',
      value: stats?.pending_claims || 0,
      color: 'from-yellow-500 to-orange-500',
      bgColor: 'bg-yellow-500/20'
    },
    {
      icon: CheckCircle,
      label: 'Approved',
      value: stats?.approved_claims || 0,
      color: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-500/20'
    },
    {
      icon: XCircle,
      label: 'Rejected',
      value: stats?.rejected_claims || 0,
      color: 'from-red-500 to-pink-500',
      bgColor: 'bg-red-500/20'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-gray-400">Welcome back! Here's your claims overview.</p>
      </motion.div>

      {/* Quick Action */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="glass p-6 rounded-xl bg-gradient-to-r from-primary-600/20 to-purple-600/20 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-4">
          <div>
            <h3 className="text-2xl font-bold mb-2">Need to file a claim?</h3>
            <p className="text-gray-300">Submit your claim in minutes with our AI-powered system</p>
          </div>
          <Link to="/dashboard/file-claim" className="btn-primary whitespace-nowrap">
            File New Claim <ArrowRight className="ml-2 inline" size={20} />
          </Link>
        </div>
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
              transition={{ delay: 0.2 + index * 0.1, duration: 0.5 }}
              className="glass p-6 rounded-xl card-hover"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon size={24} className="text-white" />
                </div>
                <Activity className="text-gray-400" size={20} />
              </div>
              <p className="text-gray-400 text-sm mb-1">{stat.label}</p>
              <p className="text-3xl font-bold gradient-text">{stat.value}</p>
            </motion.div>
          );
        })}
      </div>

      {/* Recent Claims */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="glass p-6 rounded-xl"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Recent Claims</h2>
          <Link 
            to="/dashboard/my-claims" 
            className="text-primary-400 hover:text-primary-300 flex items-center gap-2 transition-colors"
          >
            View All <ArrowRight size={18} />
          </Link>
        </div>

        {recentClaims.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto mb-4 text-gray-600" size={48} />
            <p className="text-gray-400 mb-4">No claims yet</p>
            <Link to="/dashboard/file-claim" className="btn-primary inline-block">
              File Your First Claim
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentClaims.map((claim, index) => (
              <motion.div
                key={claim._id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 + index * 0.1, duration: 0.3 }}
                className="glass-dark p-4 rounded-lg hover:bg-white/10 transition-all group"
              >
                <Link to={`/dashboard/claims/${claim._id}`} className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    <div className="p-3 bg-primary-500/20 rounded-lg">
                      <FileText className="text-primary-400" size={24} />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold mb-1">{claim.policy_number}</p>
                      <p className="text-sm text-gray-400">{claim.claim_type}</p>
                    </div>
                  </div>
                  
                  <div className="text-right mr-4">
                    <p className="font-semibold mb-1">{formatCurrency(claim.claim_amount)}</p>
                    <p className="text-sm text-gray-400">{formatDate(claim.submitted_at)}</p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(claim.status)}`}>
                      {claim.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <ArrowRight className="text-gray-400 group-hover:text-primary-400 group-hover:translate-x-1 transition-all" size={20} />
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Fraud Score Info */}
      {stats?.average_fraud_score !== undefined && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="glass p-6 rounded-xl"
        >
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <AlertTriangle className="text-blue-400" size={24} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold mb-2">AI Fraud Detection</h3>
              <p className="text-gray-400 mb-4">
                Our advanced AI system analyzes every claim for potential fraud. Your claims have an average risk score of <span className="font-bold text-primary-400">{stats.average_fraud_score.toFixed(1)}%</span>, which is considered <span className="font-bold text-green-400">LOW RISK</span>.
              </p>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-yellow-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${stats.average_fraud_score}%` }}
                />
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default CustomerDashboard;
