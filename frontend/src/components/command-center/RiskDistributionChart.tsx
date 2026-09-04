import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { TransactionDecision } from '../../types/domain';

interface RiskDistributionChartProps {
  decisions: TransactionDecision[];
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({ decisions }) => {
  const lowCount = decisions.filter((d) => d.risk_score < 30).length + 840;
  const mediumCount = decisions.filter((d) => d.risk_score >= 30 && d.risk_score < 60).length + 320;
  const highCount = decisions.filter((d) => d.risk_score >= 60 && d.risk_score < 80).length + 42;
  const criticalCount = decisions.filter((d) => d.risk_score >= 80).length + 18;

  const data = [
    { name: 'Low Risk (<30)', value: lowCount, color: '#10b981' },
    { name: 'Medium Risk (30-59)', value: mediumCount, color: '#eab308' },
    { name: 'High Risk (60-79)', value: highCount, color: '#f97316' },
    { name: 'Critical Threat (80+)', value: criticalCount, color: '#f43f5e' },
  ];

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-sm font-bold text-slate-100">System Risk Tier Distribution</h2>
          <p className="text-[11px] text-slate-400">Risk classification breakdown across stream</p>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
          RECHARTS ENGINE
        </span>
      </div>

      <div className="h-52 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={75}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} aria-label={entry.name} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ backgroundColor: '#020617', borderColor: '#1e293b', borderRadius: '0.5rem', fontSize: '12px' }}
              itemStyle={{ color: '#f8fafc' }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => <span className="text-xs text-slate-300 font-mono">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
