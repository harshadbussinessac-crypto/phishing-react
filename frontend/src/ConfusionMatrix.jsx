// matrix[actual][predicted] = [[TN, FP], [FN, TP]]
export default function ConfusionMatrix({ matrix, labels }) {
  const total = matrix.flat().reduce((a, b) => a + b, 0) || 1;
  const max = Math.max(...matrix.flat(), 1);

  return (
    <div className="cm-wrap">
      <div className="cm-title">Confusion matrix</div>
      <table className="cm">
        <thead>
          <tr>
            <th className="corner" rowSpan={2}></th>
            <th colSpan={labels.length} className="axis">Predicted</th>
          </tr>
          <tr>
            {labels.map((l) => (
              <th key={l} className="axis">{l}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th className="axis row-axis">{labels[i]}</th>
              {row.map((v, j) => {
                const intensity = 0.12 + (v / max) * 0.55;
                const correct = i === j;
                const bg = correct
                  ? `rgba(22, 163, 74, ${intensity})`
                  : `rgba(220, 38, 38, ${intensity})`;
                return (
                  <td key={j} style={{ background: bg }}>
                    <div className="cell-count">{v}</div>
                    <div className="cell-share">{((v / total) * 100).toFixed(1)}%</div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="cm-legend">
        <span><i className="dot ok" /> Correct</span>
        <span><i className="dot err" /> Error</span>
      </div>
    </div>
  );
}
