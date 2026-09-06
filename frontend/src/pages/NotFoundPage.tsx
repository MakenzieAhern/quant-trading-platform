import { Link } from "../components/Link";

export function NotFoundPage() {
  return (
    <section className="stateCallout" role="alert">
      <p className="eyebrow">ROUTE NOT FOUND</p>
      <h1>Page not found</h1>
      <p>The requested dashboard route is not available.</p>
      <Link className="button" href="/backtests">
        Return to backtests
      </Link>
    </section>
  );
}
