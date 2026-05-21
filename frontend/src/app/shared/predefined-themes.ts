export const PREDEFINED_THEMES = [
  'Pop 90s',
  'Années 80',
  'Années 2000',
  'Hits français',
  'Rap FR',
  'Rock classique',
  'Electro / Dance',
  'Disney & dessins animés',
  'Tubes récents',
  'Films & séries',
] as const;

export type PredefinedTheme = (typeof PREDEFINED_THEMES)[number];
