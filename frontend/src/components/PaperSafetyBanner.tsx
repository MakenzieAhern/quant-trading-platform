import { useTranslation } from "react-i18next";

export function PaperSafetyBanner() {
  const { t } = useTranslation("paper");
  return (
    <aside className="paperBanner" role="note" aria-label={t("safetyLabel")}>
      <strong>{t("safetyTitle")}</strong>
      <span>{t("safetyBody")}</span>
    </aside>
  );
}
