import React from 'react';
import {
  PrimaryButton,
  DefaultButton,
  IconButton,
  CompoundButton,
} from '@fluentui/react';
import type { IButtonProps } from '@fluentui/react';

// Button variants mapping
export type ButtonVariant = 
  | 'primary' 
  | 'default' 
  | 'icon' 
  | 'compound'
  | 'outline';

export type ButtonSize = 'small' | 'medium' | 'large';

interface CustomButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children?: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  icon?: string;
  secondaryText?: string;
  className?: string;
}

export const Button: React.FC<CustomButtonProps> = ({
  variant = 'default',
  size = 'medium',
  children,
  onClick,
  disabled = false,
  icon,
  secondaryText,
  className,
  ...rest
}) => {
  // Size mapping
  const sizeStyles = {
    small: { height: '32px', fontSize: '12px' },
    medium: { height: '40px', fontSize: '14px' },
    large: { height: '48px', fontSize: '16px' },
  };

  const commonProps: Partial<IButtonProps> = {
    onClick,
    disabled,
    iconProps: icon ? { iconName: icon } : undefined,
    styles: {
      root: {
        ...sizeStyles[size],
        borderRadius: '6px',
      },
    },
    className,
    ...rest,
  };

  // Render based on variant
  switch (variant) {
    case 'primary':
      return (
        <PrimaryButton
          text={children as string}
          {...commonProps}
        />
      );

    case 'icon':
      return (
        <IconButton
          iconProps={{ iconName: icon }}
          onClick={onClick}
          disabled={disabled}
          ariaLabel={children as string}
          styles={{
            root: {
              ...sizeStyles[size],
              borderRadius: '50%',
              width: sizeStyles[size].height,
            },
          }}
          className={className}
        />
      );

    case 'compound':
      return (
        <CompoundButton
          text={children as string}
          secondaryText={secondaryText}
          {...commonProps}
        />
      );

    case 'outline':
      return (
        <DefaultButton
          text={children as string}
          {...commonProps}
          styles={{
            root: {
              ...sizeStyles[size],
              borderRadius: '6px',
              border: '1px solid #0078d4',
              color: '#0078d4',
              backgroundColor: 'transparent',
              '&:hover': {
                backgroundColor: '#f3f2f1',
                borderColor: '#106ebe',
                color: '#106ebe',
              },
            },
          }}
        />
      );

    default:
      return (
        <DefaultButton
          text={children as string}
          {...commonProps}
        />
      );
  }
}; 