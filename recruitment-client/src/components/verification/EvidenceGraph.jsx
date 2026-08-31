import React from 'react';
import { Share2, User, Building2, FolderGit2, Globe, ShieldCheck } from 'lucide-react';

const getNodeIcon = (type) => {
  switch (type) {
    case 'candidate':
      return <User size={16} />;
    case 'company':
      return <Building2 size={16} />;
    case 'project':
      return <FolderGit2 size={16} />;
    case 'evidence':
    default:
      return <Globe size={16} />;
  }
};

const EvidenceGraph = ({ graphData = {} }) => {
  const nodes = graphData.nodes || [];
  const edges = graphData.edges || [];

  if (nodes.length === 0) return null;

  const candidateNode = nodes.find(n => n.type === 'candidate');
  const otherNodes = nodes.filter(n => n.type !== 'candidate');

  return (
    <div className="verif-card">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <Share2 size={18} className="verif-card-icon" />
          <h3>Candidate ↔ Company ↔ Evidence Relationship Graph</h3>
        </div>
        <span className="verif-count-pill">{nodes.length} Graph Nodes</span>
      </div>

      <div className="verif-graph-container">
        {/* Candidate Node (Center) */}
        {candidateNode && (
          <div className="verif-graph-center">
            <div className="verif-graph-node verif-node-cand">
              <User size={20} />
              <div>
                <strong>{candidateNode.label}</strong>
                <span className="verif-node-pill">Subject</span>
              </div>
            </div>
          </div>
        )}

        {/* Connected Nodes Grid */}
        <div className="verif-graph-grid">
          {otherNodes.map((n, idx) => {
            const edge = edges.find(e => e.from === n.id || e.to === n.id);
            return (
              <div key={idx} className={`verif-graph-node verif-node-${n.type}`}>
                <div className="verif-node-header">
                  <span className="verif-node-icon-wrap">{getNodeIcon(n.type)}</span>
                  <span className="verif-node-badge">{n.category || n.type}</span>
                </div>
                <h5 className="verif-node-name">{n.label}</h5>
                {edge && (
                  <span className="verif-edge-label">
                    <ShieldCheck size={11} /> {edge.label}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default EvidenceGraph;
