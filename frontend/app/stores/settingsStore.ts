import { create } from "zustand";
import { LocaleEnum, switchLanguage } from "~/i18n";

const STORAGE_KEY = "openoii-language";

function getInitialLanguage(): LocaleEnum {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved && Object.values(LocaleEnum).includes(saved as LocaleEnum)) {
    return saved as LocaleEnum;
  }
  return LocaleEnum.English;
}

interface SettingsState {
  isModalOpen: boolean;
  language: LocaleEnum;
  openModal: () => void;
  closeModal: () => void;
  setLanguage: (lang: LocaleEnum) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isModalOpen: false,
  language: getInitialLanguage(),
  openModal: () => set({ isModalOpen: true }),
  closeModal: () => set({ isModalOpen: false }),
  setLanguage: (lang: LocaleEnum) => {
    switchLanguage(lang);
    localStorage.setItem(STORAGE_KEY, lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === LocaleEnum.Arabic ? "rtl" : "ltr";
    set({ language: lang });
  },
}));