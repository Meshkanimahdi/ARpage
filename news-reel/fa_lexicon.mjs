// Spoken-side pronunciation fixes for ElevenLabs Persian TTS (user rule, 2026-10-23): brand, startup,
// product and people's names, and loanwords the voice misreads in Persian script (کد → code), are sent
// to the voice in Latin. Applied to the SPOKEN text only; on-screen text stays as written.
// Writers should already write these in Latin; this is the safety net. Extend per story with
// story.json → "lexicon": {"persian spelling": "Latin"}.
const BASE = {
  // companies, labs, products
  'اوپن ای آی': 'OpenAI', 'اپن ای آی': 'OpenAI', 'اوپن‌ای‌آی': 'OpenAI', 'چت جی پی تی': 'ChatGPT', 'جی پی تی': 'GPT',
  'آنتروپیک': 'Anthropic', 'انتروپیک': 'Anthropic', 'کلود': 'Claude', 'جمینای': 'Gemini', 'جمنای': 'Gemini',
  'گوگل': 'Google', 'مایکروسافت': 'Microsoft', 'کوپایلوت': 'Copilot', 'انویدیا': 'Nvidia', 'اینتل': 'Intel',
  'آمازون': 'Amazon', 'تسلا': 'Tesla', 'اسپیس ایکس': 'SpaceX', 'دیپ مایند': 'DeepMind', 'دیپ سیک': 'DeepSeek',
  'میدجرنی': 'Midjourney', 'میدجورنی': 'Midjourney', 'پرپلکسیتی': 'Perplexity', 'ایکس ای آی': 'xAI', 'گراک': 'Grok',
  'هاگینگ فیس': 'Hugging Face', 'رانوی': 'Runway', 'سورا': 'Sora', 'اینستاگرام': 'Instagram', 'یوتیوب': 'YouTube',
  'تیک تاک': 'TikTok', 'واتس اپ': 'WhatsApp', 'لینکدین': 'LinkedIn', 'شاپیفای': 'Shopify', 'نتفلیکس': 'Netflix',
  'ایلون ماسک': 'Elon Musk', 'ایلان ماسک': 'Elon Musk', 'سم آلتمن': 'Sam Altman', 'جنسن هوانگ': 'Jensen Huang',
  'ساندار پیچای': 'Sundar Pichai', 'داریو آمودی': 'Dario Amodei', 'مارک زاکربرگ': 'Mark Zuckerberg',
  // loanwords the voice misreads
  'کدنویسی': 'code نویسی', 'کدها': 'code ها', 'کد': 'code', 'پرامپت': 'prompt', 'پرامپت‌ها': 'prompt ها',
  'ای آی': 'AI', 'ای‌آی': 'AI', 'اپلیکیشن': 'app', 'ایجنت': 'agent', 'ایجنت‌ها': 'agent ها',
};
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
function compile(map) {
  // longest first so "چت جی پی تی" wins over "جی پی تی"; a space or ZWNJ between parts matches either
  return Object.entries(map).sort((a, b) => b[0].length - a[0].length).map(([fa, en]) =>
    [new RegExp(`(?<![\\p{L}\\p{M}])${esc(fa).replace(/[ ‌]+/g, '[\\s\\u200c]*')}(?![\\p{L}\\p{M}])`, 'gu'), en]);
}
const BASE_RX = compile(BASE);
export function latinize(text, extra) {
  let t = text;
  for (const [rx, en] of extra ? compile(extra).concat(BASE_RX) : BASE_RX) t = t.replace(rx, en);
  return t.replace(/([A-Za-z])‌/g, '$1 ').replace(/‌([A-Za-z])/g, ' $1');
}

// Persian respellings that make the Persian voice say the English name (user rule 2026-10-29: ChatGPT was read
// "chetgpt", Pro "pero"). Diacritics and ZWNJ steer the vowels; a sukun (ْ) after the first consonant of a
// cluster stops the voice inserting "e" (پْرو = "pro", not "pero"). Only a candidate: pron_test.mjs keeps it
// when an English speech-to-text hears it better than the Latin spelling.
const PRON_WORDS = {
  'ChatGPT': 'چَت‌جی‌پی‌تی', 'GPT': 'جی‌پی‌تی', 'OpenAI': 'اُپِن‌اِی‌آی', 'AI': 'اِی‌آی', 'Pro': 'پْرو', 'Plus': 'پْلاس',
  'Max': 'مَکس', 'Mini': 'مینی', 'Ultra': 'اولْترا', 'Claude': 'کْلاد', 'Anthropic': 'اَنْتروپیک', 'Gemini': 'جِمِنای',
  'Google': 'گوگِل', 'Nvidia': 'اِنْویدیا', 'Microsoft': 'مایکْروسافت', 'Copilot': 'کوپایلَت', 'Meta': 'مِتا',
  'Apple': 'اَپِل', 'iPhone': 'آیفون', 'Tesla': 'تِسْلا', 'Grok': 'گْراک', 'Sora': 'سورا', 'Perplexity': 'پِرْپِلِکْسیتی',
  'DeepSeek': 'دیپ‌سیک', 'DeepMind': 'دیپ‌مایند', 'Midjourney': 'میدْجِرنی', 'Pinterest': 'پینْتِرِست', 'Adobe': 'اَدوبی',
  'Airbnb': 'اِر‌بی‌اِن‌بی', 'Walmart': 'وال‌مارت', 'Amazon': 'اَمازون', 'Netflix': 'نِتْفلیکس', 'Spotify': 'اِسْپاتیفای',
  'YouTube': 'یوتیوب', 'Instagram': 'اینستاگْرام', 'TikTok': 'تیک‌تاک', 'LinkedIn': 'لینْکْدین', 'WhatsApp': 'واتْس‌اَپ',
  'Elon': 'ایلان', 'Musk': 'ماسک', 'Sam': 'سَم', 'Altman': 'آلْتْمَن', 'Jensen': 'جِنْسِن', 'Huang': 'هوانگ',
  'Nasdaq': 'نَزْدَک', 'IPO': 'آی‌پی‌اُو', 'app': 'اَپ', 'agent': 'اِیجِنْت', 'prompt': 'پْرامْپْت', 'code': 'کُد',
  'Science': 'ساینْس', 'Stanford': 'اِسْتَنْفورد', 'Georgia': 'جورْجیا', 'Tech': 'تِک',
};
export const PRON = new Proxy({}, {get: (_, term) => {
  if (typeof term !== 'string') return undefined;
  if (PRON_WORDS[term]) return PRON_WORDS[term];
  const parts = term.split(/\s+/);
  return parts.every(w => PRON_WORDS[w]) ? parts.map(w => PRON_WORDS[w]).join(' ') : undefined;
}});
// Latin phrases in a spoken text: runs of Latin words (ChatGPT Pro, Elon Musk, GPT-5).
export function latinTerms(text) {
  return (text.match(/[A-Za-z][A-Za-z0-9.+\-]*(?:\s+[A-Za-z0-9][A-Za-z0-9.+\-]*)*/g) || []).map(s => s.trim().replace(/[.\-]+$/, ''));
}
