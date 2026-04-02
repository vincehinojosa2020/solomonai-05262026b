// Kids Check-in shared constants and helpers
export const AVATAR_COLORS = [
  { bg: 'linear-gradient(135deg, #E11D48 0%, #F43F5E 100%)', emoji: '🦁', character: 'Daniel' },
  { bg: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)', emoji: '🐑', character: 'David' },
  { bg: 'linear-gradient(135deg, #0891B2 0%, #22D3EE 100%)', emoji: '🌊', character: 'Moses' },
  { bg: 'linear-gradient(135deg, #EA580C 0%, #FB923C 100%)', emoji: '⭐', character: 'Abraham' },
  { bg: 'linear-gradient(135deg, #059669 0%, #34D399 100%)', emoji: '🕊️', character: 'Noah' },
  { bg: 'linear-gradient(135deg, #2563EB 0%, #60A5FA 100%)', emoji: '🐋', character: 'Jonah' },
  { bg: 'linear-gradient(135deg, #DB2777 0%, #F472B6 100%)', emoji: '👑', character: 'Esther' },
  { bg: 'linear-gradient(135deg, #CA8A04 0%, #FACC15 100%)', emoji: '💪', character: 'Samson' },
];

export const getAvatarStyle = (name) => {
  const index = (name?.charCodeAt(0) || 0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
};

export const getAge = (birthdate) => {
  if (!birthdate) return null;
  const today = new Date();
  const birth = new Date(birthdate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) age--;
  return age;
};

export const formatAge = (birthdate) => {
  const age = getAge(birthdate);
  if (age === null) return 'Age not set';
  if (age === 0) return 'Under 1 year';
  if (age === 1) return '1 year old';
  return `${age} years old`;
};

export const CLASSROOMS = ['Sunday School', 'Nursery', 'Toddlers', 'Pre-K', 'Elementary', 'Pre-Teen'];
