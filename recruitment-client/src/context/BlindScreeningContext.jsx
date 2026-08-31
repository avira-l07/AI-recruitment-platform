import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';
import api from '../services/api';

const BlindScreeningContext = createContext(null);

export const BlindScreeningProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(() => authService.getCurrentUser());
  const userId = currentUser?.id || 'guest';
  const storageKey = `blind_screening_hr_${userId}`;

  // Initialize blind mode preference from localStorage for this specific HR user
  const [isBlindMode, setIsBlindModeState] = useState(() => {
    if (currentUser?.role !== 'hr') return false;
    const saved = localStorage.getItem(storageKey);
    return saved === 'true';
  });

  // Keep state synced when logged in user changes
  useEffect(() => {
    const user = authService.getCurrentUser();
    setCurrentUser(user);
    if (user?.role === 'hr') {
      const saved = localStorage.getItem(`blind_screening_hr_${user.id}`);
      setIsBlindModeState(saved === 'true');
    } else {
      setIsBlindModeState(false);
    }
  }, []);

  const sendAuditLog = async (enabled) => {
    try {
      await api.post('/activity/blind-screening-toggle', { enabled });
    } catch (err) {
      console.warn('Failed to audit blind screening toggle:', err);
    }
  };

  const setBlindMode = useCallback((value) => {
    const user = authService.getCurrentUser();
    if (!user || user.role !== 'hr') return;
    
    const nextValue = Boolean(value);
    setIsBlindModeState(nextValue);
    localStorage.setItem(`blind_screening_hr_${user.id}`, String(nextValue));
    
    // Broadcast UI sync event
    window.dispatchEvent(new CustomEvent('blind-screening-toggled', { detail: { isBlindMode: nextValue } }));
    sendAuditLog(nextValue);
  }, []);

  const toggleBlindMode = useCallback(() => {
    const user = authService.getCurrentUser();
    if (!user || user.role !== 'hr') return;

    setIsBlindModeState((prev) => {
      const nextValue = !prev;
      localStorage.setItem(`blind_screening_hr_${user.id}`, String(nextValue));
      window.dispatchEvent(new CustomEvent('blind-screening-toggled', { detail: { isBlindMode: nextValue } }));
      sendAuditLog(nextValue);
      return nextValue;
    });
  }, []);

  const getBlindIdentifier = useCallback((candidate) => {
    const id = candidate?.candidate_id || candidate?.candidateId || candidate?.id || 'Unknown';
    return `Candidate #C-${id}`;
  }, []);

  const maskEmail = useCallback((_email) => {
    return '[Concealed in Fair Review]';
  }, []);

  const maskPhone = useCallback((_phone) => {
    return '[Concealed in Fair Review]';
  }, []);

  return (
    <BlindScreeningContext.Provider
      value={{
        isBlindMode,
        setBlindMode,
        toggleBlindMode,
        getBlindIdentifier,
        maskEmail,
        maskPhone,
      }}
    >
      {children}
    </BlindScreeningContext.Provider>
  );
};

export const useBlindScreening = () => {
  const context = useContext(BlindScreeningContext);
  if (!context) {
    // Fallback safe defaults if used outside provider
    return {
      isBlindMode: false,
      setBlindMode: () => {},
      toggleBlindMode: () => {},
      getBlindIdentifier: (c) => `Candidate #C-${c?.id || 'Unknown'}`,
      maskEmail: () => '[Concealed]',
      maskPhone: () => '[Concealed]',
    };
  }
  return context;
};

export default BlindScreeningContext;
