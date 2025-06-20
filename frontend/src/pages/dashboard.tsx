import React from 'react';
import { motion } from 'framer-motion';
import {
  Stack,
  Text,
  FontWeights,
  DefaultPalette,
  Icon,
  PrimaryButton,
  DefaultButton,
} from '@fluentui/react';
import type { IStackTokens, IIconProps } from '@fluentui/react';
import { Card } from '@/components/ui/card';
import { useAuthStore } from '@/store/auth-store';

const stackTokens: IStackTokens = { childrenGap: 24 };
const cardStackTokens: IStackTokens = { childrenGap: 16 };

interface StatCardProps {
  title: string;
  value: string;
  icon: string;
  color: string;
  trend?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, trend }) => {
  const iconProps: IIconProps = { iconName: icon };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        styles={{
          padding: '24px',
          minHeight: '120px',
          border: '1px solid #e1dfdd',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          borderRadius: '8px',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
      >
        <Stack tokens={cardStackTokens}>
          <Stack horizontal horizontalAlign="space-between" verticalAlign="start">
            <div>
              <Text 
                variant="medium" 
                styles={{ 
                  root: { 
                    color: '#605e5c',
                    fontWeight: FontWeights.regular
                  } 
                }}
              >
                {title}
              </Text>
              <Text 
                variant="xLarge" 
                styles={{ 
                  root: { 
                    color: '#323130',
                    fontWeight: FontWeights.bold,
                    marginTop: '8px'
                  } 
                }}
              >
                {value}
              </Text>
            </div>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Icon {...iconProps} styles={{ root: { color: '#ffffff', fontSize: '20px' } }} />
            </div>
          </Stack>
          {trend && (
            <Text 
              variant="small" 
              styles={{ 
                root: { 
                  color: trend.startsWith('+') ? '#107c10' : trend.startsWith('-') ? '#d13438' : '#605e5c'
                } 
              }}
            >
              {trend}
            </Text>
          )}
        </Stack>
      </Card>
    </motion.div>
  );
};

interface QuickActionProps {
  title: string;
  description: string;
  icon: string;
  color: string;
  onClick: () => void;
}

const QuickActionCard: React.FC<QuickActionProps> = ({ 
  title, 
  description, 
  icon, 
  color, 
  onClick 
}) => {
  const iconProps: IIconProps = { iconName: icon };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        onClick={onClick}
        styles={{
          padding: '20px',
          border: '1px solid #e1dfdd',
          borderRadius: '8px',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
      >
        <Stack tokens={{ childrenGap: 12 }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '8px',
            backgroundColor: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Icon {...iconProps} styles={{ root: { color: '#ffffff', fontSize: '18px' } }} />
          </div>
          <div>
            <Text 
              variant="mediumPlus" 
              styles={{ 
                root: { 
                  color: '#323130',
                  fontWeight: FontWeights.semibold
                } 
              }}
            >
              {title}
            </Text>
            <Text 
              variant="small" 
              styles={{ 
                root: { 
                  color: '#605e5c',
                  marginTop: '4px'
                } 
              }}
            >
              {description}
            </Text>
          </div>
        </Stack>
      </Card>
    </motion.div>
  );
};

export const Dashboard: React.FC = () => {
  const { user } = useAuthStore();

  const stats = [
    {
      title: 'Documenti Analizzati',
      value: '2,547',
      icon: 'Document',
      color: DefaultPalette.blue,
      trend: '+12% questo mese',
    },
    {
      title: 'Conversazioni AI',
      value: '1,234',
      icon: 'Chat',
      color: DefaultPalette.green,
      trend: '+8% questa settimana',
    },
    {
      title: 'Utenti Attivi',
      value: '89',
      icon: 'People',
      color: DefaultPalette.purple,
      trend: '+3 oggi',
    },
    {
      title: 'Queries Processate',
      value: '15,672',
      icon: 'BarChart4',
      color: DefaultPalette.orange,
      trend: '+25% questo mese',
    },
  ];

  const quickActions = [
    {
      title: 'Nuova Chat AI',
      description: 'Inizia una conversazione con l\'assistente AI',
      icon: 'Chat',
      color: DefaultPalette.blue,
      onClick: () => console.log('Navigating to chat'),
    },
    {
      title: 'Carica Documento',
      description: 'Aggiungi nuovi documenti al sistema',
      icon: 'CloudUpload',
      color: DefaultPalette.green,
      onClick: () => console.log('Navigating to upload'),
    },
    {
      title: 'Visualizza Analytics',
      description: 'Controlla le metriche del sistema',
      icon: 'BarChart4',
      color: DefaultPalette.purple,
      onClick: () => console.log('Navigating to analytics'),
    },
    {
      title: 'Gestisci Utenti',
      description: 'Amministra gli utenti del sistema',
      icon: 'Settings',
      color: DefaultPalette.orange,
      onClick: () => console.log('Navigating to users'),
    },
  ];

  const filteredQuickActions = quickActions.filter(action => {
    if (action.title === 'Gestisci Utenti') {
      return user?.role === 'admin';
    }
    return true;
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{ padding: '24px' }}
    >
      <Stack tokens={stackTokens}>
        {/* Header */}
        <div>
          <Text 
            variant="xxLarge" 
            styles={{ 
              root: { 
                color: '#323130',
                fontWeight: FontWeights.semibold
              } 
            }}
          >
            Benvenuto, {user?.username}!
          </Text>
          <Text 
            variant="large" 
            styles={{ 
              root: { 
                color: '#605e5c',
                marginTop: '8px'
              } 
            }}
          >
            Ecco una panoramica del tuo portale aziendale
          </Text>
        </div>

        {/* Statistics Grid */}
        <div>
          <Text 
            variant="xLarge" 
            styles={{ 
              root: { 
                color: '#323130',
                fontWeight: FontWeights.semibold,
                marginBottom: '16px'
              } 
            }}
          >
            Statistiche
          </Text>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '16px'
          }}>
            {stats.map((stat, index) => (
              <motion.div
                key={stat.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <StatCard {...stat} />
              </motion.div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div>
          <Text 
            variant="xLarge" 
            styles={{ 
              root: { 
                color: '#323130',
                fontWeight: FontWeights.semibold,
                marginBottom: '16px'
              } 
            }}
          >
            Azioni Rapide
          </Text>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '16px'
          }}>
            {filteredQuickActions.map((action, index) => (
              <motion.div
                key={action.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <QuickActionCard {...action} />
              </motion.div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <Card
          styles={{
            padding: '24px',
            border: '1px solid #e1dfdd',
            borderRadius: '8px'
          }}
        >
          <Stack tokens={{ childrenGap: 16 }}>
            <Text 
              variant="xLarge" 
              styles={{ 
                root: { 
                  color: '#323130',
                  fontWeight: FontWeights.semibold
                } 
              }}
            >
              Attività Recenti
            </Text>
            <Stack tokens={{ childrenGap: 12 }}>
              {[
                'Documento "Report Q4" analizzato con successo',
                'Nuova conversazione AI avviata da Mario Rossi',
                'Sistema di backup completato',
                'Aggiornamento sicurezza applicato',
              ].map((activity, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  style={{
                    padding: '12px',
                    borderLeft: '4px solid #0078d4',
                    backgroundColor: '#f3f2f1',
                    borderRadius: '4px'
                  }}
                >
                  <Text 
                    variant="medium" 
                    styles={{ 
                      root: { 
                        color: '#323130'
                      } 
                    }}
                  >
                    {activity}
                  </Text>
                  <Text 
                    variant="small" 
                    styles={{ 
                      root: { 
                        color: '#605e5c',
                        marginTop: '4px'
                      } 
                    }}
                  >
                    {index + 1} {index === 0 ? 'minuto' : index < 5 ? 'minuti' : 'ore'} fa
                  </Text>
                </motion.div>
              ))}
            </Stack>
            <Stack horizontal tokens={{ childrenGap: 8 }}>
              <PrimaryButton text="Visualizza Tutto" />
              <DefaultButton text="Aggiorna" />
            </Stack>
          </Stack>
        </Card>
      </Stack>
    </motion.div>
  );
}; 