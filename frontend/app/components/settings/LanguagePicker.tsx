import { useTranslation } from "react-i18next";
import { useSettingsStore } from "~/stores/settingsStore";
import { LocaleEnum, LOCALE_LABELS } from "~/i18n";

export function LanguagePicker() {
  const { t } = useTranslation("setting");
  const { language, setLanguage } = useSettingsStore();

  return (
    <div className="space-y-4">
      <h4 className="font-bold text-sm">{t("language")}</h4>
      <select
        className="select select-bordered w-full max-w-xs"
        value={language}
        onChange={(e) => setLanguage(e.target.value as LocaleEnum)}
      >
        {Object.entries(LOCALE_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );
}
