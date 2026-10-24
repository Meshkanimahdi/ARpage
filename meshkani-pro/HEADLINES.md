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
