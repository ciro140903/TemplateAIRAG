import React from 'react';
import { Label as FluentLabel } from '@fluentui/react';
import type { ILabelProps } from '@fluentui/react';

export interface LabelProps extends ILabelProps {
  children: React.ReactNode;
  required?: boolean;
  htmlFor?: string;
}

export const Label: React.FC<LabelProps> = ({
  children,
  required = false,
  htmlFor,
  ...props
}) => {
  const labelStyles = {
    fontWeight: '600',
    fontSize: '14px',
    color: '#323130',
    marginBottom: '4px',
    display: 'block',
  };

  return (
    <div style={labelStyles}>
      <FluentLabel htmlFor={htmlFor} {...props}>
        {children}
        {required && (
          <span style={{ color: '#d13438', marginLeft: '4px' }}>*</span>
        )}
      </FluentLabel>
    </div>
  );
}; 