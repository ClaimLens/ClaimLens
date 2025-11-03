import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, Search, Filter, ArrowRight } from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDate, getStatusColor } from '../../utils/helpers';

const MyClaims = () => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      const response = await api.get('/claims/user');
      setClaims(response.data);
    } catch (error) {
      console.error('Error fetching claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredClaims = claims.filter(claim => {
    const matchesFilter = filter === 'all' || claim.status === filter;
    const matchesSearch = claim.policy_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         claim.claim_type.toLowerCase().includes(searchTerm.toLowerCase());
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
          <span className="gradient-text">My Claims</span>
        </h1>
        <p className="text-gray-400">Track and manage all your insurance claims</p>
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
              placeholder="Search by policy number or type..."
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
              onClick={() => setFilter('approved')}
              className={`px-4 py-2 rounded-lg transition-all ${
                filter === 'approved' ? 'bg-green-600 text-white' : 'glass-dark hover:bg-white/10'
              }`}
            >
              Approved
            </button>
            <button
              onClick={() => setFilter('rejected')}
              className={`px-4 py-2 rounded-lg transition-all ${
                filter === 'rejected' ? 'bg-red-600 text-white' : 'glass-dark hover:bg-white/10'
              }`}
            >
              Rejected
            </button>
          </div>
        </div>
      </div>

      {/* Claims List */}
      {filteredClaims.length === 0 ? (
        <div className="glass p-12 rounded-xl text-center">
          <FileText className="mx-auto mb-4 text-gray-600" size={64} />
          <h3 className="text-xl font-bold mb-2">No claims found</h3>
          <p className="text-gray-400 mb-6">
            {searchTerm || filter !== 'all' 
              ? 'Try adjusting your filters' 
              : 'You haven\'t filed any claims yet'
            }
          </p>
          {!searchTerm && filter === 'all' && (
            <Link to="/dashboard/file-claim" className="btn-primary inline-block">
              File Your First Claim
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredClaims.map((claim, index) => (
            <motion.div
              key={claim._id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                to={`/dashboard/claims/${claim.claim_id}`}
                className="glass p-6 rounded-xl block hover:bg-white/10 transition-all group"
              >
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="p-3 bg-primary-500/20 rounded-lg">
                      <FileText className="text-primary-400" size={24} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold">{claim.policy_number}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(claim.status)}`}>
                          {claim.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-400 mb-1">{claim.claim_type} Insurance</p>
                      <p className="text-sm text-gray-500">Submitted on {formatDate(claim.submitted_at)}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm text-gray-400 mb-1">Claim Amount</p>
                      <p className="text-2xl font-bold text-primary-400">{formatCurrency(claim.claim_amount)}</p>
                    </div>
                    <ArrowRight className="text-gray-400 group-hover:text-primary-400 group-hover:translate-x-1 transition-all" size={24} />
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyClaims;
