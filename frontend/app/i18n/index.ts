import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { resources } from './locales';

export enum LocaleEnum {
  SimplifiedChinese = 'zh-Hans',
  TraditionalChinese = 'zh-Hant',
  English = 'en-US',
  German = 'de',
  Korean = 'ko',
  Japanese = 'ja',
  French = 'fr',
  Russian = 'ru',
  Italian = 'it',
  Arabic = 'ar',
  Spanish = 'es',
  Hindi = 'hi',
}

export const LOCALE_LABELS: Record<LocaleEnum, string> = {
  [LocaleEnum.SimplifiedChinese]: '简体中文',
  [LocaleEnum.TraditionalChinese]: '繁體中文',
  [LocaleEnum.English]: 'English',
  [LocaleEnum.German]: 'Deutsch',
  [LocaleEnum.Korean]: '한국어',
  [LocaleEnum.Japanese]: '日本語',
  [LocaleEnum.French]: 'Français',
  [LocaleEnum.Russian]: 'Русский',
  [LocaleEnum.Italian]: 'Italiano',
  [LocaleEnum.Arabic]: 'العربية',
  [LocaleEnum.Spanish]: 'Español',
  [LocaleEnum.Hindi]: 'हिन्दी',
};

const STORAGE_KEY = 'openoii-language';

const savedLanguage = localStorage.getItem(STORAGE_KEY);
const systemLanguage = navigator.language.toLowerCase();
const availableLanguages = Object.values(LocaleEnum) as string[];

let initialLanguage: string;

if (savedLanguage && availableLanguages.includes(savedLanguage)) {
  initialLanguage = savedLanguage;
} else {
  const matched = availableLanguages.find((lang) =>
    systemLanguage.startsWith(lang.toLowerCase()),
  );
  initialLanguage = matched || LocaleEnum.English;
}

i18n.use(initReactI18next).init({
  resources,
  fallbackLng: LocaleEnum.English,
  lng: initialLanguage,
  ns: ['common', 'layout', 'setting', 'editor', 'project'],
  defaultNS: 'common',
  interpolation: {
    escapeValue: false,
  },
});

export const switchLanguage = (lang: LocaleEnum) => {
  i18n.changeLanguage(lang);
  localStorage.setItem(STORAGE_KEY, lang);
};

export default i18n;