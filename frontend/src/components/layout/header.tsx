import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stack,
  Text,
  SearchBox,
  IconButton,
  FontWeights,
  PersonaCoin,
  PersonaSize,
} from '@fluentui/react';
import type { IStackTokens } from '@fluentui/react';
import { useAuthStore } from '@/store/auth-store';
import { useUIStore } from '@/store/ui-store';
import { useIsDesktop, useIsTablet } from '@/hooks/use-media-query';

const headerTokens: IStackTokens = { childrenGap: 16 };

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { toggleSidebar, theme, toggleTheme } = useUIStore();
  const isDesktop = useIsDesktop();
  const isTablet = useIsTablet();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header style={{ 
      backgroundColor: '#faf9f8',
      borderBottom: '1px solid #e1dfdd',
      padding: '12px 24px'
    }}>
      <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
        {/* Left Section */}
        <Stack horizontal verticalAlign="center" tokens={headerTokens}>
          {!isDesktop && (
            <IconButton
              iconProps={{ iconName: 'GlobalNavButton' }}
              onClick={toggleSidebar}
              ariaLabel="Toggle navigation"
            />
          )}
          
                    {isDesktop && (
            <div>
              <Text 
                variant="xLarge" 
                styles={{ 
                  root: { 
                    fontWeight: FontWeights.semibold,
                    color: '#323130'
                  } 
                }}
              >
                Portale Aziendale
              </Text>
            </div>
          )}
        </Stack>

        {/* Center Section - Search */}
        <div style={{ flex: 1, maxWidth: '400px', margin: '0 16px' }}>
          <SearchBox
            placeholder="Cerca..."
            styles={{
              root: { width: '100%' }
            }}
          />
        </div>

        {/* Right Section */}
        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
          {/* Theme Toggle */}
          <IconButton
            iconProps={{ iconName: theme === 'dark' ? 'Sunny' : 'ClearNight' }}
            onClick={toggleTheme}
            ariaLabel="Cambia tema"
            title="Cambia tema"
          />

          {/* Notifications */}
          <IconButton
            iconProps={{ iconName: 'Ringer' }}
            ariaLabel="Notifiche"
            title="Notifiche"
          />

          {/* User Menu */}
          <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 12 }}>
                        {isTablet && (
              <div style={{ textAlign: 'right' }}>
                <Text 
                  variant="medium" 
                  styles={{ 
                    root: { 
                      fontWeight: FontWeights.semibold,
                      color: '#323130'
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
                      display: 'block'
                    } 
                  }}
                >
                  {user?.role}
                </Text>
              </div>
            )}
            
            <Stack horizontal tokens={{ childrenGap: 4 }}>
              <IconButton
                iconProps={{ iconName: 'Settings' }}
                onClick={() => navigate('/settings')}
                ariaLabel="Impostazioni"
                title="Impostazioni"
              />
              
              <IconButton
                iconProps={{ iconName: 'SignOut' }}
                onClick={handleLogout}
                ariaLabel="Logout"
                title="Logout"
              />

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
            </Stack>
          </Stack>
        </Stack>
      </Stack>
    </header>
  );
}; 