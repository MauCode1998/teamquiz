import React, { createContext, useState, useContext, useEffect } from 'react';
import Cookies from 'js-cookie';
import api from './api/axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('access_token');
      if (token) {
        try {
          const response = await api.get('/me');
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          Cookies.remove('access_token');
          Cookies.remove('refresh_token');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, refresh_token } = response.data;
      
      // Store tokens
      Cookies.set('access_token', access_token, { expires: 1/96 }); // 15 minutes
      Cookies.set('refresh_token', refresh_token, { expires: 7 }); // 7 days

      // Get user info
      const userResponse = await api.get('/me');
      setUser(userResponse.data);

      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (username, email, password) => {
    try {
      const response = await api.post('/register', {
        username,
        email,
        password,
      });

      const { access_token, refresh_token } = response.data;
      
      // Store tokens
      Cookies.set('access_token', access_token, { expires: 1/96 }); // 15 minutes
      Cookies.set('refresh_token', refresh_token, { expires: 7 }); // 7 days

      // Get user info
      const userResponse = await api.get('/me');
      setUser(userResponse.data);

      return { success: true };
    } catch (error) {
      console.error('Registration failed:', error);
      
      let errorMessage = 'Registration failed';
      
      if (error.response?.data) {
        // Handle FastAPI validation errors (422)
        if (error.response.data.detail) {
          if (Array.isArray(error.response.data.detail)) {
            // Validation error format: [{"msg": "...", "loc": ["body", "field"]}]
            const validationError = error.response.data.detail[0];
            if (validationError?.msg) {
              errorMessage = validationError.msg;
            }
          } else if (typeof error.response.data.detail === 'string') {
            // Simple string error message
            errorMessage = error.response.data.detail;
          }
        }
      }
      
      return { 
        success: false, 
        error: errorMessage
      };
    }
  };

  const logout = async () => {
    try {
      await api.post('/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear tokens and user data
      Cookies.remove('access_token');
      Cookies.remove('refresh_token');
      setUser(null);
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};