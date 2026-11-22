import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../translations';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('arecaguard_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    return localStorage.getItem('arecaguard_token') || null;
  });

  // Language state: defaults to saved preference or 'en'
  const [lang, setLangState] = useState(() => {
    return localStorage.getItem('arecaguard_lang') || 'en';
  });

  const t = translations[lang] || translations.en;

  const setLanguage = (newLang) => {
    if (newLang === 'en' || newLang === 'kn') {
      setLangState(newLang);
      localStorage.setItem('arecaguard_lang', newLang);
      if (token && user) {
        fetch('/api/auth/update-language', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ language_preference: newLang })
        }).catch(() => {});
      }
    }
  };

  const login = async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed. Please check credentials.');
    }

    const data = await res.json();
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('arecaguard_token', data.access_token);
    localStorage.setItem('arecaguard_user', JSON.stringify(data.user));

    if (data.user?.language_preference) {
      setLanguage(data.user.language_preference);
    }
    return data;
  };

  const register = async (name, email, password) => {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        password,
        language_preference: lang
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed.');
    }

    const data = await res.json();
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('arecaguard_token', data.access_token);
    localStorage.setItem('arecaguard_user', JSON.stringify(data.user));
    return data;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('arecaguard_token');
    localStorage.removeItem('arecaguard_user');
    fetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      lang,
      setLanguage,
      t,
      login,
      register,
      logout,
      isAuthenticated: !!token && !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
