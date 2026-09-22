import { performance } from "node:perf_hooks";
import console from "node:console";
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { createServer } from "vite";

const server = await createServer({ server: { middlewareMode: true } });
try {
    const { EquityChart } = await server.ssrLoadModule(
        "/src/components/EquityChart.tsx",
    );
    const points = Array.from({ length: 200 }, (_, index) => ({
        timestamp: new Date(Date.UTC(2024, 0, index + 1)).toISOString(),
        equity: String(100000 + index),
        cash: "100000",
        market_value: String(index),
    }));
    const durations = [];
    for (let iteration = 0; iteration < 11; iteration += 1) {
        const start = performance.now();
        const markup = renderToString(createElement(EquityChart, { points }));
        if (!markup.includes("100199"))
            throw new Error("missing exact final equity");
        if (iteration > 0) durations.push(performance.now() - start);
    }
    durations.sort((a, b) => a - b);
    console.info(
        JSON.stringify({
            points: 200,
            samples: 10,
            median_render_ms: durations[5],
        }),
    );
} finally {
    await server.close();
}
