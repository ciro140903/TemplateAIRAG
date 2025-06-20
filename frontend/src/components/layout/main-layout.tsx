import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Outlet } from 'react-router-dom';

import { Header } from './header';
import { Sidebar } from './sidebar';
import { useUIStore } from '@/store/ui-store';

export const MainLayout: React.FC = () => {
  const { sidebarOpen } = useUIStore();

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            style={{ 
              position: 'relative',
              backgroundColor: '#faf9f8',
              borderRight: '1px solid #e1dfdd',
              overflow: 'hidden'
            }}
          >
            <Sidebar />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <Header />
        
        {/* Main Content */}
        <main style={{ flex: 1, overflowY: 'auto', backgroundColor: '#ffffff' }}>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
            style={{ 
              minHeight: '100%',
              padding: '24px',
              maxWidth: sidebarOpen ? 'none' : '100%'
            }}
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
}; 