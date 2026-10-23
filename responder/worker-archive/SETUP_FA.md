# راه‌اندازی یک‌باره (مسیر Composio، بدون اپ Meta) — حدود ۲۰ دقیقه

هیچ کلیدی را در چت ننویس. کلیدها فقط در داشبورد Cloudflare (بخش Secret) وارد می‌شوند.

## واقعیت درباره سرعت
Composio برای کامنت و دایرکت اینستاگرام **تریگر push** ندارد (پیدا نکردم؛ اکشن وبهوک آن هم یک اپ Live در Meta می‌خواهد). پس سرویس هر ~۱۰ ثانیه صندوق را چک می‌کند (poll). نتیجه:
- تأخیر واقعی از لحظه نوشتن کامنت تا انتشار پاسخ: میانگین حدود ۷–۸ ثانیه، p95 حدود ۱۲–۱۴ ثانیه (نصف فاصله poll + ۲ تا ۳ ثانیه پردازش).
- **زیر ۵ ثانیه روی این مسیر تضمین نمی‌شود.** poll هر ۲ ثانیه ممکن است ولی سهمیه Composio و محدودیت اینستاگرام را می‌سوزاند و پیشنهادش نمی‌کنم.
- اگر روزی اپ Meta گرفتی، همین کد با `TRANSPORT="meta"` وبهوک واقعی دارد و به ~۳ ثانیه می‌رسد.
- هر دور poll روی حساب بی‌صدا فقط ۲ تماس Composio است (کامنت فقط وقتی تعداد کامنت پست عوض شود خوانده می‌شود).

## ۱) کلیدها
1. **COMPOSIO_API_KEY**: وارد dashboard.composio.dev شو ← Settings ← API Keys ← یک کلید جدید برای همین سرویس بساز و کپی کن.
2. **ANTHROPIC_API_KEY**: console.anthropic.com ← API Keys ← Create Key (نام: meshkani-responder).
3. **ADMIN_TOKEN**: یک رشته تصادفی بلند (۳۲+ حرف) که خودت می‌سازی؛ برای گزارش‌گیری و روشن/خاموش کردن poller.
4. **شناسه اکانت Composio برای meshkani.pro**: در Composio ← Connected accounts ← اکانت اینستاگرام `meshkani.pro` ← شناسه‌اش (شبیه `ca_...`). توجه: اکانت‌های `mirror.dev` و `mahdi.meshkani` هم وصل‌اند؛ سرویس فقط با شناسه صریح کار می‌کند و اگر اکانت اشتباه باشد خودش متوقف می‌شود. این شناسه محرمانه نیست؛ همین‌جا به من بگو.

## ۲) Cloudflare
1. در dash.cloudflare.com اکانت رایگان بساز (Durable Objects روی پلن رایگان با SQLite کار می‌کند؛ اگر خطای پلن داد، پلن Workers Paid حدود ۵ دلار در ماه).
2. Storage & Databases ← KV ← Create namespace با نام `RESPONDER_KV` ← شناسه را به من بگو.
3. Workers & Pages ← Create ← **Import a repository** ← ریپوی `ARpage`، شاخه `claude/ecstatic-davinci-1lqsug`، **Root directory = `responder`**، Build command خالی، Deploy command `npx wrangler deploy`.
4. بعد از اولین دیپلوی: Worker ← Settings ← Variables and Secrets ← سه Secret بالا را به‌صورت **Secret** وارد کن: `COMPOSIO_API_KEY`، `ANTHROPIC_API_KEY`، `ADMIN_TOKEN`.

## ۳) بعد از شما
من شناسه KV و شناسه اکانت را در `wrangler.toml` می‌گذارم، با `DRY_RUN=1` (فقط تصمیم و لاگ) poller را روشن می‌کنم، با یک کامنت تست از حساب شخصی‌ات زمان واقعی را اندازه می‌گیرم و عدد واقعی را به تو می‌گویم. فقط بعد از تأیید تو `DRY_RUN=0` می‌شود.

## هزینه
- مدل (Sonnet 5.5، ورودی ۲$ و خروجی ۱۰$ به ازای میلیون توکن): حدود **۳ تا ۸ دلار به ازای ۱۰۰۰ پاسخ**. مورد نادیده‌گرفته‌شده فقط هزینه ورودی دارد؛ پیش‌فیلترها رایگان‌اند.
- Composio: ~۱۷٬۰۰۰ تماس در روز در حالت poll هر ۱۰ ثانیه؛ باید با سهمیه پلن Composio چک شود (نمی‌دانم پلنت چقدر اجازه می‌دهد). می‌شود شب‌ها poll را کندتر کرد.
- Cloudflare: Worker و KV در این حجم تقریباً رایگان.
