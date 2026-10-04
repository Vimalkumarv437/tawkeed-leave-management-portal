import React, { useEffect, ReactNode } from 'react';
import { IconX } from './Icons';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export default function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  size = 'md',
}: ModalProps): React.ReactElement | null {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-xl',
    lg: 'max-w-2xl',
    xl: 'max-w-3xl',
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex min-h-full items-center justify-center p-3 sm:p-4 md:p-6 text-center"
      onClick={onClose}
    >
      <div
        className={`w-full ${sizeClasses[size] || 'max-w-xl'} my-auto flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200/80 text-left align-middle overflow-hidden transform transition-all duration-200 max-h-[calc(100dvh-2rem)] sm:max-h-[calc(100dvh-3.5rem)]`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between px-5 sm:px-6 py-4 border-b border-slate-100 bg-slate-50/80 shrink-0 gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight leading-snug">{title}</h3>
            {subtitle && <p className="text-xs text-slate-500 mt-1 leading-normal">{subtitle}</p>}
          </div>
          <button
            type="button"
            className="p-1.5 -mr-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors shrink-0 cursor-pointer focus:outline-hidden"
            onClick={onClose}
            aria-label="Close modal"
          >
            <IconX size={18} />
          </button>
        </div>
        <div className="p-5 sm:p-6 overflow-y-auto flex-1 overscroll-contain">
          {children}
        </div>
      </div>
    </div>
  );
}
