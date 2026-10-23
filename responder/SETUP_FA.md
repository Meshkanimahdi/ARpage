# راه‌اندازی یک‌باره (برای مهدی) — حدود ۳۰ تا ۴۵ دقیقه

هیچ کلیدی را در چت ننویس. همه‌چیز فقط در داشبورد هاست (Cloudflare) و Meta وارد می‌شود.

## الف) اپ Meta
1. به developers.facebook.com برو → My Apps → Create App → نوع **Business**.
2. محصول **Instagram** را اضافه کن، گزینه **API setup with Instagram login**.
3. حساب `meshkani.pro` را (باید Professional باشد) اضافه کن و **Generate token** بزن. توکن را فقط در مرحله «ج» استفاده کن.
4. در **App settings → Basic** مقدار **App Secret** را ببین (فقط برای مرحله «ج»).
5. مجوزها: `instagram_business_basic`، `instagram_business_manage_comments`، `instagram_business_manage_messages`.
6. تا وقتی اپ در حالت Development است فقط حساب‌های Tester (خودت و تیمت) کار می‌کنند. برای کاربران واقعی باید **App Review** و **Live mode** بگیری (مجوزهای بالا را درخواست کن؛ ویدیوی کوتاه از کارکرد لازم است). تست‌های من با حساب خودت انجام می‌شود.

## ب) Cloudflare
1. در dash.cloudflare.com اکانت (رایگان کافی است) بساز.
2. KV: Storage → KV → Create namespace با نام `RESPONDER_KV`؛ شناسه‌اش را به من بگو (شناسه مخفی نیست).
3. Workers → Create → Worker با نام `meshkani-responder`؛ کد را من از ریپو دیپلوی می‌کنم (مرحله بعد از اتمام کارهای شما).

## ج) متغیرهای محرمانه (Settings → Variables and Secrets → Secret)
| نام | مقدار |
|---|---|
| `ANTHROPIC_API_KEY` | کلید API آنتروپیک (یک کلید مخصوص همین سرویس بساز) |
| `IG_ACCESS_TOKEN` | توکن مرحله الف-۳ (long-lived؛ هر ~۶۰ روز تمدید) |
| `IG_APP_SECRET` | App Secret مرحله الف-۴ |
| `WEBHOOK_VERIFY_TOKEN` | یک رشته تصادفی بلند که خودت می‌سازی |
| `ADMIN_TOKEN` | یک رشته تصادفی بلند دیگر (برای گزارش‌گیری من) |

## د) وبهوک
Meta → Instagram → API setup → Webhooks:
- Callback URL: `https://<آدرس-worker>/webhook` (بعد از دیپلوی به تو می‌دهم)
- Verify token: همان `WEBHOOK_VERIFY_TOKEN`
- Subscribe به فیلدهای **comments** و **messages** برای `meshkani.pro`.

## بعد از شما
من دیپلوی می‌کنم (حالت `DRY_RUN=1`: فقط تصمیم و لاگ، بدون پاسخ واقعی)، با کامنت تست از حساب Tester تأخیر را اندازه می‌گیرم، و فقط بعد از تأیید زیر ۵ ثانیه `DRY_RUN=0` را روشن می‌کنم.

## هزینه و تأخیر (تخمین، بعد از تست واقعی دقیق می‌شود)
- تأخیر: وبهوک تا پاسخ منتشرشده معمولاً ۲ تا ۳٫۵ ثانیه (مدل با تلاش کم و بدون thinking ≈ ۱–۲ ثانیه + ارسال اینستاگرام). هدف p95 ≤ ۵ ثانیه؛ هر رویداد زمانش لاگ می‌شود.
- هزینه به ازای ۱۰۰۰ پاسخ: حدود **۳ تا ۸ دلار** (Sonnet 5.5: ورودی ۲$ و خروجی ۱۰$ به ازای هر میلیون توکن؛ پرامپت سیستم کش می‌شود، اما در ترافیک کم کش گاهی منقضی می‌شود و سمت بالای بازه را می‌دهد). مورد نادیده‌گرفته‌شده فقط هزینه ورودی دارد و موارد پیش‌فیلتر شده رایگان‌اند. Cloudflare Workers و KV در حجم این پیج رایگان است.

## مسیر جایگزین (فقط اگر خودت بگویی «بله»)
Composio triggers به‌جای اپ Meta؛ نیاز به کلید API Composio روی سرور دارد. بدون تأیید صریح تو استفاده نمی‌شود.
