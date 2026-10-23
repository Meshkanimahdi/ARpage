# Pixel art card battle game

- **id:** `159-pixel-art-card-battle-game` · **category:** PIXEL (Pixel art and retro graphics)
- **source:** https://prompt-motion.com/aisongman-71ffac · **creator:** @aisongman
- **use:** مناسب معرفی بازی، مکانیک بازی یا محتوای سرگرمی برای بازیکنان.
- **visual style:** پیکسل‌آرت و گرافیک رترو
- **mood:** مدرن و هدف‌محور · **audience:** بازیکنان و علاقه‌مندان موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** متوسط تا زیاد در نمونه‌کار و محتوای بصری؛ وابسته به اجرا و پلتفرم
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Make a 1-on-1 card game like Hearthstone, as good as you can, in pixel art.
A full playable loop: decks, mana, minions, spells, attacking, a simple but fair AI opponent, a win and a loss screen.
Juice every action: cards lift, flip and slam, hits shake the target, numbers pop.
Banned: placeholder rectangles, unreadable card text, anything that looks like a tech demo.
</direction>

<structure>
A title screen, a match, and a result screen that lets me play again.
</structure>

<build>
1. One HTML file, canvas or DOM, no build step. All art drawn in code on a strict pixel grid.
2. Sound effects written with the Web Audio API.
3. Play a full match yourself and fix anything broken or unfair.
</build>

<start>
List the cards and rules in a few lines, then build it without asking me anything else.
</start>
````
