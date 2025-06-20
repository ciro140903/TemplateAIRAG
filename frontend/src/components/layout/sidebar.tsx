import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Nav,
  Stack,
  Text,
  FontWeights,
  PersonaCoin,
  PersonaSize,
} from '@fluentui/react';
import type { INavLink } from '@fluentui/react';
import { useAuthStore } from '@/store/auth-store';
import type { MenuItem } from '@/types/ui';

const navigationItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/dashboard',
    icon: 'Home',
  },
  {
    id: 'chat',
    label: 'Chat AI',
    href: '/chat',
    icon: 'Chat',
  },
  {
    id: 'documents',
    label: 'Documenti',
    href: '/documents',
    icon: 'Document',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    href: '/analytics',
    icon: 'BarChart4',
    roles: ['admin', 'user'],
  },
  {
    id: 'users',
    label: 'Utenti',
    href: '/admin/users',
    icon: 'People',
    roles: ['admin'],
  },
  {
    id: 'settings',
    label: 'Impostazioni',
    href: '/settings',
    icon: 'Settings',
  },
  {
    id: 'security',
    label: 'Sicurezza',
    href: '/security',
    icon: 'Shield',
  },
  {
    id: 'help',
    label: 'Aiuto',
    href: '/help',
    icon: 'Help',
  },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const filteredItems = navigationItems.filter(item => {
    if (!item.roles) return true;
    return user?.role && item.roles.includes(user.role);
  });

  const navLinks: INavLink[] = filteredItems.map((item) => ({
    name: item.label,
    url: item.href || '',
    icon: item.icon,
    key: item.id,
    onClick: (ev?: React.MouseEvent<HTMLElement>, item?: INavLink) => {
      ev?.preventDefault();
      if (item?.url) {
        navigate(item.url);
      }
    },
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Logo/Brand */}
      <div style={{ 
        padding: '24px',
        borderBottom: '1px solid #e1dfdd'
      }}>
        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 12 }}>
          <div style={{
            width: '32px',
            height: '32px',
            backgroundColor: '#0078d4',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Text 
              styles={{ 
                root: { 
                  color: '#ffffff',
                  fontWeight: FontWeights.bold,
                  fontSize: '14px'
                } 
              }}
            >
              P
            </Text>
          </div>
          <div>
            <Text 
              variant="medium" 
              styles={{ 
                root: { 
                  fontWeight: FontWeights.semibold,
                  color: '#323130'
                } 
              }}
            >
              Portale
            </Text>
            <Text 
              variant="small" 
              styles={{ 
                root: { 
                  color: '#605e5c',
                  display: 'block'
                } 
              }}
            >
              Aziendale
            </Text>
          </div>
        </Stack>
      </div>

      {/* Navigation */}
      <div style={{ flex: 1, padding: '16px' }}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Nav
            groups={[
              {
                links: navLinks
              }
            ]}
            selectedKey={location.pathname}
            styles={{
              root: {
                width: '100%'
              },
              link: {
                height: '40px',
                paddingLeft: '12px',
                paddingRight: '12px',
              },
              linkText: {
                fontSize: '14px',
                fontWeight: FontWeights.regular,
              }
            }}
          />
        </motion.div>
      </div>

      {/* User Info */}
      <div style={{ 
        padding: '16px',
        borderTop: '1px solid #e1dfdd'
      }}>
        <Stack 
          horizontal 
          verticalAlign="center" 
          tokens={{ childrenGap: 12 }}
          styles={{
            root: {
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: '#f3f2f1'
            }
          }}
        >
          <PersonaCoin
            text={user?.username}
            size={PersonaSize.size32}
            styles={{
              coin: {
                backgroundColor: '#0078d4',
                color: '#ffffff'
              }
            }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <Text 
              variant="medium" 
              styles={{ 
                root: { 
                  fontWeight: FontWeights.semibold,
                  color: '#323130',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                } 
              }}
            >
              {user?.username}
            </Text>
            <Text 
              variant="small" 
              styles={{ 
                root: { 
                  color: '#605e5c',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                } 
              }}
            >
              {user?.email}
            </Text>
          </div>
        </Stack>
      </div>
    </div>
  );
}; 