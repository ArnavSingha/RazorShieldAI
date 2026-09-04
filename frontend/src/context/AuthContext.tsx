import React, { createContext, useContext, useState, useEffect } from 'react';

export type UserRole = 'RISK_ANALYST' | 'OPERATOR' | 'AUDITOR' | 'ADMIN';

export interface UserProfile {
  principal_id: string;
  name: string;
  role: UserRole;
  token: string;
}

interface AuthContextType {
  user: UserProfile;
  devSimRole: UserRole;
  setDevSimRole: (role: UserRole) => void;
  hasCapability: (capability: string) => boolean;
}

const ROLE_CAPABILITIES: Record<UserRole, string[]> = {
  AUDITOR: [
    'investigation.read',
    'transaction.read',
    'audit.read',
  ],
  OPERATOR: [
    'investigation.read',
    'transaction.read',
    'action.review',
    'action.execute',
    'audit.read',
  ],
  RISK_ANALYST: [
    'investigation.read',
    'investigation.update',
    'investigation.assign',
    'investigation.resolve',
    'transaction.read',
    'ai.run',
    'action.review',
    'action.authorize',
    'action.execute',
    'audit.read',
    'case.export',
  ],
  ADMIN: [
    'investigation.read',
    'investigation.update',
    'investigation.assign',
    'investigation.resolve',
    'transaction.read',
    'ai.run',
    'action.review',
    'action.authorize',
    'action.execute',
    'audit.read',
    'case.export',
    'simulation.run',
    'chaos.control',
  ],
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [devSimRole, setDevSimRoleState] = useState<UserRole>(() => {
    const saved = localStorage.getItem('razorshield_sim_role') as UserRole;
    return saved && ROLE_CAPABILITIES[saved] ? saved : 'RISK_ANALYST';
  });

  const setDevSimRole = (role: UserRole) => {
    localStorage.setItem('razorshield_sim_role', role);
    setDevSimRoleState(role);
  };

  const user: UserProfile = {
    principal_id: devSimRole === 'ADMIN' ? 'usr_admin_01' : devSimRole === 'AUDITOR' ? 'usr_auditor_01' : devSimRole === 'OPERATOR' ? 'usr_operator_01' : 'usr_analyst_01',
    name: devSimRole === 'ADMIN' ? 'Admin Operator' : devSimRole === 'AUDITOR' ? 'Auditor Compliance' : devSimRole === 'OPERATOR' ? 'Merchant Operator' : 'Arnav Singha',
    role: devSimRole,
    token: `Bearer ${devSimRole.toLowerCase()}_secret_token_123`,
  };

  const hasCapability = (capability: string): boolean => {
    const caps = ROLE_CAPABILITIES[devSimRole] || [];
    return caps.includes(capability);
  };

  return (
    <AuthContext.Provider value={{ user, devSimRole, setDevSimRole, hasCapability }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
