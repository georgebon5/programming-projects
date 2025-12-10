import React from 'react';

const variantClasses = {
  // Status variants
  active: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-blue-100 text-blue-800',
  rejected: 'bg-red-100 text-red-800',
  funded: 'bg-indigo-100 text-indigo-800',
  in_progress: 'bg-cyan-100 text-cyan-800',

  // Category variants
  infrastructure: 'bg-gray-200 text-gray-800',
  environment: 'bg-teal-100 text-teal-800',
  community: 'bg-purple-100 text-purple-800',
  parks: 'bg-lime-100 text-lime-800',
  culture: 'bg-pink-100 text-pink-800',
  safety: 'bg-orange-100 text-orange-800',
  other: 'bg-indigo-100 text-indigo-800',
  
  // Default
  default: 'bg-gray-100 text-gray-800',
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: keyof typeof variantClasses;
  className?: string;
}

export default function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const classes = variantClasses[variant] || variantClasses.default;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${classes} ${className}`}
    >
      {children}
    </span>
  );
}
