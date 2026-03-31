import { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../utils/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Hydrate user on app load - always fetch fresh data from /api/auth/me if token exists
  useEffect(() => {
    const hydrateUser = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const data = await authAPI.getMe();
        setUser(data.user);
        localStorage.setItem('user', JSON.stringify(data.user));
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setUser(null);
        navigate('/auth');
      } finally {
        setLoading(false);
      }
    };

    hydrateUser();
  }, [navigate]);

  const login = async (identifier, password) => {
    const data = await authAPI.login(identifier, password);

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);

    return data;
  };

  const register = async (userData) => {
    const data = await authAPI.register(userData);

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);

    return data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    navigate('/auth');
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
