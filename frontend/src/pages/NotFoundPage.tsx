import { Link } from "../components/Link";
import { useTranslation } from "react-i18next";

export function NotFoundPage() {
  const { t } = useTranslation("common");
  return (
    <section className="stateCallout" role="alert">
      <p className="eyebrow">{t("routeNotFound")}</p>
      <h1>{t("pageNotFound")}</h1>
      <p>{t("pageNotFoundBody")}</p>
      <Link className="button" href="/backtests">
        {t("returnToBacktests")}
      </Link>
    </section>
  );
}
