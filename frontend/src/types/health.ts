export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  broker_mode: "backtest" | "paper";
}
