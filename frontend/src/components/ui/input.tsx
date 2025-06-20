import React from 'react';
import { TextField } from '@fluentui/react';
import type { ITextFieldProps } from '@fluentui/react';

export interface InputProps extends Omit<ITextFieldProps, 'type'> {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
}

export const Input: React.FC<InputProps> = ({
  type = 'text',
  label,
  placeholder,
  required,
  disabled,
  errorMessage,
  value,
  onChange,
  onBlur,
  onFocus,
  multiline = false,
  styles,
  ...props
}) => {
  const inputStyles = {
    root: {
      marginBottom: '16px',
    },
    fieldGroup: {
      borderRadius: '6px',
      border: errorMessage ? '2px solid #d13438' : '1px solid #d2d0ce',
      backgroundColor: disabled ? '#f3f2f1' : '#ffffff',
      '&:hover': {
        borderColor: errorMessage ? '#d13438' : '#323130',
      },
      '&:focus': {
        borderColor: '#0078d4',
        borderWidth: '2px',
      },
    },
    field: {
      fontSize: '14px',
      color: '#323130',
      padding: '8px 12px',
      '&::placeholder': {
        color: '#605e5c',
      },
    },
    ...styles,
  };

  return (
    <TextField
      type={type}
      label={label}
      placeholder={placeholder}
      required={required}
      disabled={disabled}
      errorMessage={errorMessage}
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      onFocus={onFocus}
      multiline={multiline}
      styles={inputStyles}
      {...props}
    />
  );
}; 