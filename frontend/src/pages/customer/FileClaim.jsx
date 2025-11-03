import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  Upload, 
  CheckCircle, 
  ArrowRight, 
  ArrowLeft,
  File,
  X
} from 'lucide-react';
import api from '../../utils/api';
import toast from 'react-hot-toast';

const FileClaim = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    policy_number: '',
    claim_type: 'Health',
    claim_amount: '',
    incident_date: '',
    description: '',
  });
  
  const [files, setFiles] = useState([]);

  const steps = [
    { icon: FileText, label: 'Claim Details', desc: 'Basic information' },
    { icon: Upload, label: 'Upload Documents', desc: 'Supporting files' },
    { icon: CheckCircle, label: 'Review & Submit', desc: 'Confirm details' }
  ];

  const claimTypes = ['Health', 'Motor', 'Property', 'Life', 'Travel'];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles([...files, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    setLoading(true);
    
    try {
      const formDataToSend = new FormData();
      Object.keys(formData).forEach(key => {
        formDataToSend.append(key, formData[key]);
      });
      
      files.forEach(file => {
        formDataToSend.append('documents', file);
      });

      const response = await api.post('/claims/create', formDataToSend, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success('Claim submitted successfully!');
      navigate(`/dashboard/claims/${response.data.claim_id}`);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to submit claim');
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    if (currentStep === 0) {
      return formData.policy_number && formData.claim_amount && formData.incident_date && formData.description;
    }
    if (currentStep === 1) {
      return files.length > 0;
    }
    return true;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">File New Claim</span>
        </h1>
        <p className="text-gray-400">Complete the steps below to submit your insurance claim</p>
      </motion.div>

      {/* Stepper */}
      <div className="glass p-6 rounded-xl mb-8">
        <div className="flex items-center justify-between relative">
          {/* Progress Line */}
          <div className="absolute top-6 left-0 right-0 h-1 bg-gray-700">
            <motion.div
              className="h-full bg-gradient-to-r from-primary-500 to-purple-500"
              initial={{ width: '0%' }}
              animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          {/* Steps */}
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            
            return (
              <div key={index} className="flex flex-col items-center relative z-10 flex-1">
                <motion.div
                  initial={{ scale: 0.8 }}
                  animate={{ scale: isCurrent ? 1.1 : 1 }}
                  className={`
                    w-12 h-12 rounded-full flex items-center justify-center mb-3
                    transition-all duration-300
                    ${isCompleted 
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                      : isCurrent 
                        ? 'bg-gradient-to-r from-primary-500 to-purple-500 ring-4 ring-primary-500/30' 
                        : 'bg-gray-700'
                    }
                  `}
                >
                  <Icon size={24} className="text-white" />
                </motion.div>
                <p className={`text-sm font-medium text-center ${isCurrent ? 'text-white' : 'text-gray-400'}`}>
                  {step.label}
                </p>
                <p className="text-xs text-gray-500 text-center">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Form Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="glass p-8 rounded-xl"
        >
          {currentStep === 0 && (
            <div className="space-y-6">
              <h3 className="text-2xl font-bold mb-6">Claim Information</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">Policy Number *</label>
                <input
                  type="text"
                  name="policy_number"
                  value={formData.policy_number}
                  onChange={handleChange}
                  className="input-glass w-full"
                  placeholder="POL10012345"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Claim Type *</label>
                <select
                  name="claim_type"
                  value={formData.claim_type}
                  onChange={handleChange}
                  className="input-glass w-full"
                  required
                >
                  {claimTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Claim Amount (₹) *</label>
                <input
                  type="number"
                  name="claim_amount"
                  value={formData.claim_amount}
                  onChange={handleChange}
                  className="input-glass w-full"
                  placeholder="50000"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Incident Date *</label>
                <input
                  type="date"
                  name="incident_date"
                  value={formData.incident_date}
                  onChange={handleChange}
                  className="input-glass w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description *</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  className="input-glass w-full h-32 resize-none"
                  placeholder="Describe the incident in detail..."
                  required
                />
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-6">
              <h3 className="text-2xl font-bold mb-6">Upload Documents</h3>
              
              <div className="border-2 border-dashed border-gray-600 rounded-xl p-8 text-center hover:border-primary-500 transition-colors">
                <input
                  type="file"
                  multiple
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                  accept="image/*,.pdf"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="mx-auto mb-4 text-gray-400" size={48} />
                  <p className="text-lg font-medium mb-2">Click to upload documents</p>
                  <p className="text-sm text-gray-400">Support for images and PDF files</p>
                </label>
              </div>

              {files.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm font-medium">Selected Files ({files.length})</p>
                  {files.map((file, index) => (
                    <div key={index} className="glass-dark p-4 rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <File className="text-primary-400" size={24} />
                        <div>
                          <p className="font-medium">{file.name}</p>
                          <p className="text-sm text-gray-400">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                      >
                        <X className="text-red-400" size={20} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <h3 className="text-2xl font-bold mb-6">Review Your Claim</h3>
              
              <div className="space-y-4">
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Policy Number</p>
                  <p className="font-semibold">{formData.policy_number}</p>
                </div>
                
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Claim Type</p>
                  <p className="font-semibold">{formData.claim_type}</p>
                </div>
                
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Claim Amount</p>
                  <p className="font-semibold text-primary-400">₹{Number(formData.claim_amount).toLocaleString('en-IN')}</p>
                </div>
                
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Incident Date</p>
                  <p className="font-semibold">{formData.incident_date}</p>
                </div>
                
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Description</p>
                  <p className="font-semibold">{formData.description}</p>
                </div>
                
                <div className="glass-dark p-4 rounded-lg">
                  <p className="text-sm text-gray-400 mb-1">Documents</p>
                  <p className="font-semibold">{files.length} file(s) attached</p>
                </div>
              </div>

              <div className="glass-dark p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                <p className="text-sm text-blue-300">
                  ℹ️ Your claim will be analyzed by our AI system and reviewed within 24-48 hours.
                </p>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation Buttons */}
      <div className="flex justify-between mt-8">
        <button
          onClick={prevStep}
          disabled={currentStep === 0}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <ArrowLeft size={20} /> Previous
        </button>
        
        <button
          onClick={nextStep}
          disabled={!canProceed() || loading}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white" />
              Processing...
            </>
          ) : currentStep === steps.length - 1 ? (
            <>Submit Claim <CheckCircle size={20} /></>
          ) : (
            <>Next <ArrowRight size={20} /></>
          )}
        </button>
      </div>
    </div>
  );
};

export default FileClaim;
