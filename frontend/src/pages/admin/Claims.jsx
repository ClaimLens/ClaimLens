import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, Search, Filter, CheckCircle, XCircle, Eye, AlertTriangle } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate, getStatusColor, getFraudScoreColor } from '../../utils/helpers';
import toast from 'react-hot-toast';

const AdminClaims = () => {
  const [searchParams] = useSearchParams();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(searchParams.get('status') || 'all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      const response = await api.get('/admin/claims');
      setClaims(response.data);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (claimId, action) => {
    try {
      await api.put(`/admin/claims/${claimId}/${action}`);
      toast.success(`Claim ${action}d successfully!`);
      fetchClaims();
    } catch (error) {
      toast.error(error.response?.data?.error || `Failed to ${action} claim`);
    }
  };

  const filteredClaims = claims.filter(claim => {
    const matchesFilter = filter === 'all' || claim.status === filter;
    const matchesSearch = claim.policy_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         claim.user_email?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">Claims Management</span>
        </h1>
        <p className="text-gray-400">Review and process insurance claims</p>
      </motion.div>

      {/* Filters */}
      <div className="glass p-6 rounded-xl mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by policy number or email..."
              className="input-glass w-full pl-11"
            />
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg transition-all ${
                filter === 'all' ? 'bg-primary-600 text-white' : 'glass-dark hover:bg-white/10'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('pending')}
              className={`px-4 py-2 rounded-lg transition-all ${
                filter === 'pending' ? 'bg-yellow-600 text-white' : 'glass-dark hover:bg-white/10'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => setFilter('under_review')}
              className={`px-4 py-2 rounded-lg transition-all ${
                filter === 'under_review' ? 'bg-blue-600 text-white' : 'glass-dark hover:bg-white/10'
              }`}
            >
              Review
            </button>
            <button
              onClick={() => setFilter('approved')}
              className={`px-4 py-2 rounded-lg transition-all ${
                filter === 'approved' ? 'bg-green-600 text-white' : 'glass-dark hover:bg-white/10'
              }`}
            >
              Approved
            </button>
          </div>
        </div>
      </div>

      {/* Claims Table */}
      {filteredClaims.length === 0 ? (
        <div className="glass p-12 rounded-xl text-center">
          <FileText className="mx-auto mb-4 text-gray-600" size={64} />
          <h3 className="text-xl font-bold mb-2">No claims found</h3>
          <p className="text-gray-400">Try adjusting your filters</p>
        </div>
      ) : (
        <div className="glass rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Policy</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Customer</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Type</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Amount</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Risk</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Status</th>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {filteredClaims.map((claim, index) => (
                  <motion.tr
                    key={claim._id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-white/5 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="font-medium">{claim.policy_number}</div>
                      <div className="text-sm text-gray-400">{formatDate(claim.submitted_at)}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">{claim.user_email || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm">{claim.claim_type}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-medium">{formatCurrency(claim.claim_amount)}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {claim.fraud_score >= 60 && (
                          <AlertTriangle className="text-red-400" size={16} />
                        )}
                        <span className={`font-medium ${getFraudScoreColor(claim.fraud_score)}`}>
                          {claim.fraud_score.toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(claim.status)}`}>
                        {claim.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {claim.status === 'pending' || claim.status === 'under_review' ? (
                          <>
                            <button
                              onClick={() => handleAction(claim._id, 'approve')}
                              className="p-2 bg-green-500/20 hover:bg-green-500/30 rounded-lg transition-colors"
                              title="Approve"
                            >
                              <CheckCircle className="text-green-400" size={18} />
                            </button>
                            <button
                              onClick={() => handleAction(claim._id, 'reject')}
                              className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg transition-colors"
                              title="Reject"
                            >
                              <XCircle className="text-red-400" size={18} />
                            </button>
                          </>
                        ) : null}
                        <Link
                          to={`/dashboard/claims/${claim._id}`}
                          className="p-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <Eye className="text-blue-400" size={18} />
                        </Link>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminClaims;
