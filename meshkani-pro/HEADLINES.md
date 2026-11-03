# Cover and hook headlines: playbook and scoring (user rule 2026-10-24)

Mahdi: «تیتر روی کاورها خیلی مهمه… مردم حالشون از کلمهٔ هوش مصنوعی به هم می‌خوره… باید از تیترهای جنجالی‌تر،
عموم‌پسندتر و تحریک‌کننده‌تر استفاده کنیم.» ("The cover headline matters a lot… people are sick of the word
'AI'… we need more controversial, more mass-appeal, more provocative headlines.")

Every reel cover headline, every carousel slide-1 headline, the first line of every caption and the first
spoken line of a reel go through this system.

## What the page's own data says (snapshot 2026-10-24, reach)
| reach | headline / first line | why it worked or failed |
|---|---|---|
| **77,857** | «اگه می‌خوای شغلت امن بمونه… لوله‌کش شو؟» ("If you want your job to stay safe… become a plumber?") | personal stake (your job), a shocking practical command, no "AI" word in the hook |
| **41,016** | cover: «مسعود پزشکیان / رئیس‌جمهور» (political gasoline reel) | a famous, polarising name everyone recognises, plus a public controversy |
| 1,709 | «هوش مصنوعی ۲ برابر پزشک‌ها؟» ("AI twice as good as doctors?") | starts with "هوش مصنوعی" (AI); weak stake for the viewer |
| 1,539 | «دیروز چند دولت اروپایی عمداً سایت‌هاشون رو خاموش کردن…» ("Yesterday several European governments deliberately took their websites offline…") | intriguing, but long and far from the viewer's life |
| 1,395 | «یه ایجنت هوش مصنوعی، هشدارهای تیم امنیتی خودش رو قطع کرد…» ("An AI agent switched off its own security team's alerts…") | AI words first, jargon (ایجنت = agent) |
| 312 | «هر خبری که باید از دنیای هوش مصنوعی بدونی…» ("Every story you need to know from the world of AI…") | generic, AI word, no stake |

Lesson: the winning headlines talk about **the viewer's job, money, family or a famous person**, with
tension. They never lead with "هوش مصنوعی" (AI). The AI angle belongs inside the reel, not on the cover.

## Rules
1. **AI fatigue.** No «هوش مصنوعی» (AI), «AI», «ایجنت» (agent), «مدل» (model), «چت‌بات» (chatbot) or
   «الگوریتم» (algorithm) in a cover headline, unless the cover is about a famous AI brand everyone
   knows (ChatGPT) and even then never as the first word. Name the *effect on people* instead: «ماشین»
   (machine), «ربات» (robot), «یه برنامه» (an app), «کامپیوتر» (computer), or no tech word at all.
2. **Stakes first.** Job, salary, money, rent, children, health, exams, migration, phone, car, fuel,
   internet, Instagram itself: things a general Persian audience feels today.
3. **Power names.** Famous, recognisable people or brands (presidents, Musk, Apple, Google, Instagram,
   footballers, celebrities) carry reach. Use a name **only when the story is really about them**.
4. **Tension.** Use contrast, a ban, a firing, a secret, a fight, a "they don't want you to know", a
   reversal, or a command («… شو», «… نکن», «… رو پاک کن»: "become …", "don't …", "delete …").
5. **Short.** 2–6 words on the cover, one accent word, no full stop. The kicker (1–3 words) can carry
   context such as «فوری» ("breaking"), «جنجالی» ("controversial") or the brand.
6. **Truth gate, never optional.** Provocative is fine; false is not. Every name, number and claim in
   the headline must be in the dossier's `allowed_claims`. Put a question mark on anything uncertain.
   Never invent quotes or attach a public figure who is not in the story. No ethnic, religious or
   sectarian incitement, no harassment of private people, no medical scare, and no fake "breaking".
   Political names are allowed when the story is about them, stated neutrally (a question or a fact),
   never as an insult.

## Process (each reel cover, each post slide 1)
1. **Write 14 candidates** across these angles, 2 each (A–G):
   - **A. personal stake:** your job, money or family;
   - **B. power name:** a famous person or brand in the story;
   - **C. conflict:** a ban, a fight, a firing, a secret;
   - **D. contrarian or command:** «… شو» ("become …"), «… نکن» ("don't …"), "everyone is wrong
     about …";
   - **E. question to the viewer:** "would you …?";
   - **F. shock number:** a number from the claims, framed for a person;
   - **G. job / life-group call-out (user rule 2026-10-24):** name the group the story touches and promise or
     warn it: «اگه آشپزی، این به دردت می‌خوره», «آرایشگرها منتظر باشن», «اونایی که می‌خوان لاغر شن خوشحال
     باشن». True to the story, respectful (speak to the goal, never shame a body or a class).
2. **Score them:**
   `python3 meshkani-pro/scripts/headline_score.py --facts work/story/dossier.json --cands work/story/headlines.txt`
   This checks the length, the AI-fatigue words, the stake, name, tension, question and number signals,
   the truth gate (names and numbers must appear in the facts) and novelty against the last 14 covers in
   `_automation/insights.json`. It returns a ranked list.
3. **Pick the winner yourself** from the top 3, judging the score, the story's emotion and
   `insights.json → leaders.headline_angle`. Write it and the runner-up to the slot file as
   `cover.headline {text, angle, score, runner_up}`. The caption's first line and the reel's first
   spoken line use the same angle; they do not need to be the same words.
4. **Learning.** The daily ANALYTICS run (RUNBOOK §6) joins each item's reach and its 3 s hold with
   `cover.headline.angle` and its features. It keeps `leaders.headline_angle` and
   `headline_lessons` in insights.json and adds new winning words to
   `meshkani-pro/headline_lexicon.json` (in the `learned` key, via a commit). Each week, rank the
   angles by median reach. Keep 1 cover in 4 on an under-tested angle.

## Angle H — your life, your family (user rule 2026-11-01, the strongest angle so far)
Speak to the viewer's own money, job, safety, health or family, as a question or a direct "you":
«اگه می‌خوای شغلت امن بمونه… لوله‌کش شو؟» (116k views), «خودتو برای جنگ آماده کردی؟» (59k in 14 h),
«همه می‌دونن…» (311k). Score +4 in headline_score.py when the headline names the viewer («تو»، «شغلت»، «پولت»،
«خانواده‌ت») and a concrete life stake.

## Angle N — the hard number contrast (user rule 2026-11-03, Mahdi's own example, top priority for money/work/data topics)
Mahdi on the last reel's cover: «کاور همین ریلز اخر میتونست خیلی جذاب‌تر باشه: "۳.۵ ساعت کار در ازای فقط ۱ دلار" —
"درآمد یک ایرانی"». What makes it work:
- **Two concrete numbers in one line, set against each other** (effort vs reward, before vs after, them vs us):
  «۳.۵ ساعت کار ← ۱ دلار». The viewer does the maths in half a second and feels it.
- **The word «فقط»** (or «همه‌ش»، «کمتر از») turns a fact into an injustice.
- **The kicker names whose life it is, in 2–3 plain words:** «درآمد یک ایرانی». No label, no AI word, no «از دید…».
- Numbers are real and sourced (allowed_claims): official wage ÷ free-market dollar rate, with the date.
- The reel's first spoken line says the same contrast; the AI angle comes inside the reel (what AI changes for
  that hour of work, or how to earn in dollars), never on the cover.
Pattern: `<number> <unit of effort/cost> در ازای فقط <number> <unit of reward>` + kicker `<whose life>`.
More of the same shape: «۱۸ میلیون حقوق = ۱۵۰ دلار»، «یه ماه اجاره = ۴ ماه حقوق»، «۸ ساعت کار ← ۲ لیتر روغن».
For every reel on money, work, prices or time, at least one of the 12 candidates must be an angle-N headline,
and it wins whenever its numbers are sourced.

## Angle W — the "what if" that puts the viewer inside the danger (user rule 2026-11-03, Mahdi)
Mahdi on REEL-034 (cover «صدای بچه‌ات بود، ولی خودش نبود»): «تیترش هم باید اینطوری می‌شد: "اگه بچت پشت تلفن نباشه چی؟" —
تیترها باید جنجالی و با هوک قوی باشه».
- **Why the old one was weak:** it is a statement that gives away the twist (the voice was fake). The viewer
  already knows the end, so there is nothing to watch for. headline_score.py now takes 3 points off this
  "X بود، ولی Y نبود" spoiler shape.
- **Why the new one wins:** «اگه … چی؟» drops the viewer into their own worst moment (your child, your money, your
  phone), opens a question only the reel answers, and is short, spoken Persian (بچت، نباشه).
- Pattern: `اگه <your person/thing> <the unthinkable> چی؟` — «اگه بچت پشت تلفن نباشه چی؟»، «اگه فردا حسابت خالی
  باشه چی؟»، «اگه صدای خودت علیه خودت باشه چی؟». +4 in headline_score.py.
- **Every cover must be controversial with a strong hook** (§00.18, §00.20): it either opens a loop (W), sets two
  hard numbers against each other (N), or names the viewer's own stake (H). A cover that only describes or
  summarises the story is rejected at the concept gate, whatever its score.
- Never reveal the twist, the answer or the ending on the cover; the cover asks, the reel answers.
