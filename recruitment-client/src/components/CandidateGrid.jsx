import React from 'react';

const CandidateGrid = ({ children, selectAllChecked, onSelectAll }) => {
  return (
    <div className="hr-table-wrapper" style={{ overflowX: 'auto', width: '100%' }}>
      <table className="hr-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
            <th style={{ width: '40px', padding: 'var(--space-4) var(--space-5)' }}>
              <input
                type="checkbox"
                className="hr-check"
                checked={selectAllChecked}
                onChange={onSelectAll}
                style={{ cursor: 'pointer' }}
              />
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Rank
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Candidate
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Matched Skills
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Matched Job
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Score
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              AI Source
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Status
            </th>
            <th style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {children}
        </tbody>
      </table>
    </div>
  );
};

export default CandidateGrid;
