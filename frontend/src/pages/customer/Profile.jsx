import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { User, Mail, Phone, Shield, Calendar, Edit, Save } from 'lucide-react';
import toast from 'react-hot-toast';

const Profile = () => {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
  });

  const handleSave = () => {
    // API call to update profile would go here
    toast.success('Profile updated successfully!');
    setIsEditing(false);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold mb-2">
          <span className="gradient-text">Profile</span>
        </h1>
        <p className="text-gray-400">Manage your account information</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass p-8 rounded-xl"
      >
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold">Personal Information</h2>
          <button
            onClick={() => isEditing ? handleSave() : setIsEditing(true)}
            className="btn-primary flex items-center gap-2"
          >
            {isEditing ? (
              <>
                <Save size={20} /> Save Changes
              </>
            ) : (
              <>
                <Edit size={20} /> Edit Profile
              </>
            )}
          </button>
        </div>

        <div className="space-y-6">
          <div className="glass-dark p-6 rounded-lg">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-primary-500/20 rounded-lg">
                <User className="text-primary-400" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Full Name</p>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="input-glass mt-1"
                  />
                ) : (
                  <p className="text-lg font-semibold">{user?.full_name}</p>
                )}
              </div>
            </div>
          </div>

          <div className="glass-dark p-6 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <Mail className="text-blue-400" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Email Address</p>
                <p className="text-lg font-semibold">{user?.email}</p>
              </div>
            </div>
          </div>

          <div className="glass-dark p-6 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-500/20 rounded-lg">
                <Phone className="text-green-400" size={24} />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-400">Phone Number</p>
                {isEditing ? (
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="input-glass mt-1"
                  />
                ) : (
                  <p className="text-lg font-semibold">{user?.phone || 'Not provided'}</p>
                )}
              </div>
            </div>
          </div>

          <div className="glass-dark p-6 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-500/20 rounded-lg">
                <Shield className="text-purple-400" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Account Type</p>
                <p className="text-lg font-semibold uppercase">{user?.role}</p>
              </div>
            </div>
          </div>

          <div className="glass-dark p-6 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-500/20 rounded-lg">
                <Calendar className="text-orange-400" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">Member Since</p>
                <p className="text-lg font-semibold">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-IN', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  }) : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Profile;
