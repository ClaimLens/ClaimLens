import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  FileText,
  Calendar,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Download,
  Shield
} from 'lucide-react';
import api from '../../utils/api';
import { formatCurrency, formatDateTime, getStatusColor, getFraudScoreColor, getFraudScoreLabel } from '../../utils/helpers';

const ClaimDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [claim, setClaim] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClaimDetails();
  }, [id]);

  const fetchClaimDetails = async () => {
    try {
      const response = await api.get(`/claims/${id}`);
      setClaim(response.data);
    } catch (error) {
      console.error('Error fetching claim details:', error);
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

  if (!claim) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400 mb-4">Claim not found</p>
        <button onClick={() => navigate('/dashboard/my-claims')} className="btn-primary">
          Back to Claims
        </button>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (claim.status) {
      case 'approved':
        return <CheckCircle className="text-green-400" size={32} />;
      case 'rejected':
        return <XCircle className="text-red-400" size={32} />;
      case 'under_review':
        return <Clock className="text-blue-400" size={32} />;
      default:
        return <Clock className="text-yellow-400" size={32} />;
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <button
        onClick={() => navigate('/dashboard/my-claims')}
        className="btn-secondary mb-6 flex items-center gap-2"
      >
        <ArrowLeft size={20} /> Back to Claims
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header Card */}
        <div className="glass p-8 rounded-xl">
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-4 mb-3">
                <h1 className="text-3xl font-bold">{claim.policy_number}</h1>
                <span className={`px-4 py-2 rounded-full font-medium ${getStatusColor(claim.status)}`}>
                  {claim.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <p className="text-gray-400">Claim ID: {claim._id}</p>
            </div>
            {getStatusIcon()}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-dark p-4 rounded-lg">
              <FileText className="text-primary-400 mb-2" size={24} />
              <p className="text-sm text-gray-400 mb-1">Claim Type</p>
              <p className="text-xl font-bold">{claim.claim_type}</p>
            </div>
            
            <div className="glass-dark p-4 rounded-lg">
              <DollarSign className="text-green-400 mb-2" size={24} />
              <p className="text-sm text-gray-400 mb-1">Claim Amount</p>
              <p className="text-xl font-bold text-primary-400">{formatCurrency(claim.claim_amount)}</p>
            </div>
            
            <div className="glass-dark p-4 rounded-lg">
              <Calendar className="text-blue-400 mb-2" size={24} />
              <p className="text-sm text-gray-400 mb-1">Submitted</p>
              <p className="text-xl font-bold">{formatDateTime(claim.submitted_at)}</p>
            </div>
          </div>
        </div>

        {/* Fraud Score */}
        <div className="glass p-6 rounded-xl">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <Shield className="text-purple-400" size={24} />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold mb-2">AI Fraud Analysis</h3>
              <p className="text-gray-400 mb-4">
                Our AI system has analyzed this claim for potential fraud indicators
              </p>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="flex-1">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-400">Risk Score</span>
                    <span className={`text-sm font-bold ${getFraudScoreColor(claim.fraud_score)}`}>
                      {claim.fraud_score.toFixed(1)}% - {getFraudScoreLabel(claim.fraud_score)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-3">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${claim.fraud_score}%` }}
                      transition={{ duration: 1, delay: 0.3 }}
                      className={`h-3 rounded-full ${
                        claim.fraud_score >= 80 ? 'bg-red-500' :
                        claim.fraud_score >= 60 ? 'bg-orange-500' :
                        claim.fraud_score >= 30 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                    />
                  </div>
                </div>
              </div>

              {claim.fraud_indicators && claim.fraud_indicators.length > 0 && (
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm font-medium mb-2">Detected Indicators:</p>
                  <ul className="space-y-1">
                    {claim.fraud_indicators.map((indicator, index) => (
                      <li key={index} className="text-sm text-gray-400 flex items-center gap-2">
                        <AlertTriangle size={14} className="text-yellow-400" />
                        {indicator}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="glass p-6 rounded-xl">
          <h3 className="text-xl font-bold mb-4">Incident Description</h3>
          <p className="text-gray-300 leading-relaxed">{claim.description}</p>
        </div>

        {/* AI Extracted Data */}
        {claim.ai_extracted_data && Object.keys(claim.ai_extracted_data).length > 0 && (
          <div className="glass p-6 rounded-xl">
            <h3 className="text-xl font-bold mb-4">AI Extracted Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(claim.ai_extracted_data).map(([key, value]) => (
                <div key={key} className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1 capitalize">{key.replace(/_/g, ' ')}</p>
                  <p className="font-medium">{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Documents */}
        {claim.documents && claim.documents.length > 0 && (
          <div className="glass p-6 rounded-xl">
            <h3 className="text-xl font-bold mb-4">Uploaded Documents</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {claim.documents.map((doc, index) => (
                <div key={index} className="glass-dark p-4 rounded-lg flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="text-primary-400" size={24} />
                    <span className="font-medium">Document {index + 1}</span>
                  </div>
                  <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                    <Download size={20} className="text-primary-400" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Admin Comments */}
        {claim.admin_comments && (
          <div className="glass p-6 rounded-xl bg-blue-500/10 border border-blue-500/30">
            <h3 className="text-xl font-bold mb-2">Admin Comments</h3>
            <p className="text-gray-300">{claim.admin_comments}</p>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default ClaimDetails;
