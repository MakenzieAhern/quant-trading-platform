import type { EquityPoint } from "../types/backtests";
import { formatDecimal, formatUtc } from "../utils/format";

const WIDTH = 900;
const HEIGHT = 260;
const PAD = 28;

export function EquityChart({ points }: { points: EquityPoint[] }) {
  if (points.length === 0) return null;
  // Number conversion is confined to SVG coordinates; labels retain exact API strings.
  const values = points.map((point) => Number(point.equity));
  const finite = values.every(Number.isFinite);
  const minimum = finite ? Math.min(...values) : 0;
  const maximum = finite ? Math.max(...values) : 0;
  const spread = Math.max(maximum - minimum, Math.abs(maximum) * 0.001, 1);
  const coordinates = finite
    ? values.map((value, index) => {
        const x =
          PAD + (index / Math.max(points.length - 1, 1)) * (WIDTH - PAD * 2);
        const y =
          HEIGHT - PAD - ((value - minimum) / spread) * (HEIGHT - PAD * 2);
        return `${x},${y}`;
      })
    : [];

  return (
    <figure className="chartCard">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-labelledby="equity-title equity-desc"
      >
        <title id="equity-title">Portfolio equity curve</title>
        <desc id="equity-desc">
          Equity over UTC time in deterministic API order.
        </desc>
        <line x1={PAD} x2={WIDTH - PAD} y1={HEIGHT - PAD} y2={HEIGHT - PAD} />
        <line x1={PAD} x2={PAD} y1={PAD} y2={HEIGHT - PAD} />
        {finite ? (
          <polyline points={coordinates.join(" ")} />
        ) : (
          <text x="50%" y="50%" textAnchor="middle">
            Chart geometry unavailable; exact values remain below.
          </text>
        )}
      </svg>
      <figcaption>
        <span>{formatUtc(points[0]?.timestamp ?? null)}</span>
        <strong>{formatDecimal(points.at(-1)?.equity ?? null)}</strong>
        <span>{formatUtc(points.at(-1)?.timestamp ?? null)}</span>
      </figcaption>
      <details>
        <summary>Accessible equity data ({points.length} points)</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">UTC time</th>
              <th scope="col">Equity</th>
            </tr>
          </thead>
          <tbody>
            {points.map((point, index) => (
              <tr key={`${point.timestamp}-${index}`}>
                <td>{formatUtc(point.timestamp)}</td>
                <td>{point.equity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
