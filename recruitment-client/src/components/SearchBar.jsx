import React from 'react';
import { Search } from 'lucide-react';

const SearchBar = ({ value, onChange, placeholder = 'Search...', style }) => {
  return (
    <div 
      className="hr-search-bar" 
      style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 'var(--space-3)', 
        backgroundColor: '#F8FAFC', 
        border: '1px solid var(--color-border)', 
        borderRadius: 'var(--radius-md)', 
        padding: 'var(--space-2) var(--space-4)', 
        width: '100%', 
        ...style 
      }}
    >
      <Search size={16} style={{ color: 'var(--color-muted)', flexShrink: 0 }} />
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={{
          border: 'none',
          background: 'transparent',
          outline: 'none',
          fontSize: 'var(--font-sm)',
          fontFamily: 'inherit',
          color: 'var(--color-text)',
          width: '100%'
        }}
      />
    </div>
  );
};

export default SearchBar;
