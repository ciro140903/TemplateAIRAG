import React from 'react';
import { 
  Stack, 
  mergeStyles, 
  IStackProps,
  getTheme,
  ITheme
} from '@fluentui/react';

export interface CardProps extends Omit<IStackProps, 'styles'> {
  children: React.ReactNode;
  elevated?: boolean;
  hoverable?: boolean;
  padding?: number | string;
  styles?: {
    padding?: string;
    minHeight?: string;
    border?: string;
    boxShadow?: string;
    borderRadius?: string;
    cursor?: string;
    transition?: string;
    backgroundColor?: string;
  };
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  elevated = false,
  hoverable = false,
  padding = '16px',
  styles = {},
  onClick,
  ...stackProps
}) => {
  const theme: ITheme = getTheme();

  const cardClass = mergeStyles({
    backgroundColor: theme.palette.white,
    border: `1px solid ${theme.palette.neutralLight}`,
    borderRadius: '8px',
    padding: typeof padding === 'number' ? `${padding}px` : padding,
    transition: 'all 0.2s ease-in-out',
    cursor: onClick || hoverable ? 'pointer' : 'default',
    
    // Shadow based on elevation
    boxShadow: elevated 
      ? theme.effects.elevation8 
      : theme.effects.elevation4,
    
    // Hover effects
    ':hover': hoverable || onClick ? {
      boxShadow: theme.effects.elevation8,
      transform: 'translateY(-1px)',
      borderColor: theme.palette.neutralTertiary,
    } : {},
    
    // Focus effects for accessibility
    ':focus': {
      outline: `2px solid ${theme.palette.themePrimary}`,
      outlineOffset: '2px',
    },
    
    // Custom styles override
    ...styles,
  });

  const handleClick = onClick ? () => onClick() : undefined;
  const handleKeyPress = onClick ? (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick();
    }
  } : undefined;

  return (
    <Stack
      {...stackProps}
      className={cardClass}
      onClick={handleClick}
      onKeyPress={handleKeyPress}
      tabIndex={onClick ? 0 : undefined}
      role={onClick ? 'button' : 'region'}
      aria-label={onClick ? 'Clickable card' : undefined}
    >
      {children}
    </Stack>
  );
};

// Varianti predefinite
export const StatCard: React.FC<CardProps> = (props) => (
  <Card
    elevated
    hoverable
    padding="24px"
    styles={{
      minHeight: '120px',
      ...props.styles,
    }}
    {...props}
  />
);

export const ActionCard: React.FC<CardProps> = (props) => (
  <Card
    hoverable
    padding="20px"
    styles={{
      cursor: 'pointer',
      ...props.styles,
    }}
    {...props}
  />
);

export const InfoCard: React.FC<CardProps> = (props) => (
  <Card
    padding="16px"
    styles={{
      backgroundColor: '#f8f9fa',
      border: '1px solid #e9ecef',
      ...props.styles,
    }}
    {...props}
  />
);

 