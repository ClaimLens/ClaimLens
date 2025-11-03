import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Zap, 
  Brain, 
  FileCheck, 
  TrendingUp, 
  Lock,
  ArrowRight,
  CheckCircle,
  Sparkles
} from 'lucide-react';

const LandingPage = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Advanced NLP and ML models analyze claims in seconds, extracting key information automatically.',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: Shield,
      title: 'Fraud Detection',
      description: 'Real-time anomaly detection identifies suspicious patterns with 95%+ accuracy.',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: Zap,
      title: '70% Faster Processing',
      description: 'Automated workflows reduce claim processing time from days to hours.',
      color: 'from-orange-500 to-red-500'
    },
    {
      icon: FileCheck,
      title: 'Smart OCR',
      description: 'Extract and validate document data automatically with Tesseract OCR engine.',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: TrendingUp,
      title: 'Predictive Analytics',
      description: 'Get insights on claim trends, approval rates, and risk patterns.',
      color: 'from-yellow-500 to-orange-500'
    },
    {
      icon: Lock,
      title: 'Secure & Compliant',
      description: 'Bank-grade encryption with IRDAI compliance and data protection.',
      color: 'from-indigo-500 to-purple-500'
    }
  ];

  const stats = [
    { value: '70%', label: 'Faster Processing' },
    { value: '95%', label: 'Fraud Detection Accuracy' },
    { value: '60%', label: 'Cost Reduction' },
    { value: '24/7', label: 'Availability' }
  ];

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary-500/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-float animation-delay-400" />
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl animate-float animation-delay-200" />
      </div>

      {/* Navigation */}
      <nav className="relative glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Shield className="text-primary-400" size={32} />
              <span className="text-2xl font-bold gradient-text">ClaimLens</span>
            </div>
            <div className="flex gap-4">
              <Link to="/login" className="btn-secondary">
                Login
              </Link>
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-6">
            <Sparkles className="text-yellow-400" size={16} />
            <span className="text-sm">AI-Powered Insurance Automation</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="gradient-text">Transform</span> Insurance Claims
            <br />with <span className="gradient-text">AI Intelligence</span>
          </h1>
          
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Automate claim processing, detect fraud in real-time, and deliver instant decisions 
            with our cutting-edge AI platform. Built for the future of insurance.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2">
              Start Free Trial <ArrowRight size={20} />
            </Link>
            <button className="btn-secondary">
              Watch Demo
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 + index * 0.1, duration: 0.5 }}
                className="glass p-6 rounded-xl text-center"
              >
                <div className="text-3xl md:text-4xl font-bold gradient-text mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Powerful Features for <span className="gradient-text">Smart Claims</span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Everything you need to modernize your insurance claim workflow
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.05, y: -5 }}
                className="glass p-6 rounded-xl hover:shadow-2xl hover:shadow-primary-500/20 transition-all duration-300 group"
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} p-3 mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className="text-white" size={24} />
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* How It Works */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            How <span className="gradient-text">ClaimLens</span> Works
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-4 gap-6">
          {[
            { step: '01', title: 'Submit Claim', desc: 'Upload documents and fill simple form' },
            { step: '02', title: 'AI Analysis', desc: 'Our AI extracts and verifies data instantly' },
            { step: '03', title: 'Fraud Check', desc: 'Advanced ML detects anomalies automatically' },
            { step: '04', title: 'Get Decision', desc: 'Receive instant approval or review status' }
          ].map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.15, duration: 0.5 }}
              viewport={{ once: true }}
              className="relative glass p-6 rounded-xl text-center"
            >
              <div className="text-6xl font-bold text-primary-500/20 mb-4">{item.step}</div>
              <CheckCircle className="mx-auto mb-4 text-green-400" size={32} />
              <h3 className="text-lg font-bold mb-2">{item.title}</h3>
              <p className="text-sm text-gray-400">{item.desc}</p>
              
              {index < 3 && (
                <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-6">
                  <ArrowRight className="text-primary-500" />
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="glass p-12 rounded-2xl text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-primary-600/20 to-purple-600/20" />
          <div className="relative z-10">
            <h2 className="text-4xl font-bold mb-4">
              Ready to <span className="gradient-text">Transform</span> Your Claims?
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Join hundreds of insurers automating their claim workflow
            </p>
            <Link to="/register" className="btn-primary inline-flex items-center gap-2">
              Get Started Free <ArrowRight size={20} />
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-white/10 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="text-primary-400" size={24} />
              <span className="font-bold gradient-text">ClaimLens</span>
            </div>
            <p className="text-gray-400 text-sm">
              © 2025 ClaimLens. Built with ❤️ for Hackathon
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
