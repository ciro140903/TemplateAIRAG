import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/pages/login';
import { Dashboard } from '@/pages/dashboard';
import { MainLayout } from '@/components/layout/main-layout';
import { ProtectedRoute } from './protected-route';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected Routes */}
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="chat" element={<div>Chat AI - Coming Soon</div>} />
        <Route path="documents" element={<div>Documenti - Coming Soon</div>} />
        <Route path="analytics" element={<div>Analytics - Coming Soon</div>} />
        <Route path="settings" element={<div>Impostazioni - Coming Soon</div>} />
        <Route path="security" element={<div>Sicurezza - Coming Soon</div>} />
        <Route path="help" element={<div>Aiuto - Coming Soon</div>} />
        
        {/* Admin Routes */}
        <Route 
          path="admin/users" 
          element={
            <ProtectedRoute requiredRole="admin">
              <div>Gestione Utenti - Coming Soon</div>
            </ProtectedRoute>
          } 
        />
        
        {/* Default redirect */}
        <Route path="" element={<Navigate to="/dashboard" replace />} />
      </Route>
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}; 