/* ===== Shared model of the apartment. Plan coords in metres: x to the right, y down the sheet. ===== */
window.HOME = (function () {
  const ROOMS = [
    { id: "main", name: "اتاق اصلی", sub: "خواب + نشیمن + آشپزخانه‌ی دیواری", x: 2.4, y: 0, w: 4.8, h: 6.8, lx: 5.6, ly: 5.55, floor: "wood" },
    { id: "kitchen", name: "آشپزخانه", sub: "اجاق، سینک، پکیج", x: 2.4, y: 6.8, w: 2.65, h: 2.2, lx: 3.7, ly: 7.75, tile: true, floor: "green" },
    { id: "nook", name: "ناهارخوری", sub: "میز ۴ نفره", x: 5.05, y: 6.8, w: 2.15, h: 2.2, lx: 6.12, ly: 7.1, tile: true, floor: "green" },
    { id: "entry", name: "ورودی", sub: "جاکفشی و آینه", x: 0, y: 2.15, w: 2.4, h: 1.25, lx: 1.05, ly: 2.9, floor: "wood" },
    { id: "bath", name: "حمام", sub: "دوش + روشویی + توالت", x: 0, y: 0.4, w: 1.7, h: 1.75, lx: 1.05, ly: 1.62, tile: true, floor: "beige" },
    { id: "lobby", name: "پیش‌ورودی حمام", sub: "", x: 1.7, y: 0.4, w: 0.7, h: 1.75, lx: 2.05, ly: 1.0, small: true, floor: "wood" },
  ];
  // wall centrelines [x1, y1, x2, y2, thickness]
  const WALLS = [
    [2.4, 0, 7.2, 0, .25], [7.2, 0, 7.2, .55, .3], [7.2, 1.75, 7.2, 9, .3],
    [7.2, 9, 6.98, 9, .3], [5.3, 9, 4.9, 9, .3], [4.35, 9, 2.4, 9, .3], [2.4, 9, 2.4, 6.8, .25],
    [2.4, 6.8, 2.4, 3.2, .2], [2.4, 2.3, 2.4, 2.1, .2], [2.4, 1.3, 2.4, 0, .25],
    [0, .4, 2.4, .4, .25], [0, .4, 0, 2.35, .25], [0, 3.25, 0, 3.4, .25], [0, 3.4, 2.4, 3.4, .25],
    [1.7, .4, 1.7, 1.3, .12], [1.7, 2.02, 1.7, 2.15, .12], [0, 2.15, 2.4, 2.15, .12],
    [2.4, 6.8, 3.65, 6.8, .25], [4.5, 6.8, 5.85, 6.8, .25], [6.95, 6.8, 7.2, 6.8, .25],
    [5.05, 6.8, 5.05, 9, .12],
  ];
  const WINDOWS = [
    { x1: 7.2, y1: .55, x2: 7.2, y2: 1.75, t: .3, sill: .8, head: 2.3 },
    { x1: 5.3, y1: 9, x2: 6.98, y2: 9, t: .3, sill: .75, head: 2.4 },
    { x1: 4.35, y1: 9, x2: 4.9, y2: 9, t: .3, sill: .95, head: 2.3 },
  ];
  const OPENINGS = [
    { x1: 3.65, y1: 6.8, x2: 4.5, y2: 6.8, t: .25, type: "arch" },
    { x1: 5.85, y1: 6.8, x2: 6.95, y2: 6.8, t: .25, type: "arch" },
    { x1: 2.4, y1: 2.3, x2: 2.4, y2: 3.2, t: .2, type: "open", head: 2.1 },
    { x1: 2.4, y1: 1.3, x2: 2.4, y2: 2.1, t: .2, type: "open", head: 2.1 },
    { x1: 1.7, y1: 1.3, x2: 1.7, y2: 2.02, t: .12, type: "door", head: 2.02 },
    { x1: 0, y1: 2.35, x2: 0, y2: 3.25, t: .25, type: "front", head: 2.05 },
  ];
  // walls get a half-thickness extension at corners, but stop flush where an opening or window starts
  const ends = [];
  WINDOWS.concat(OPENINGS).forEach((o) => ends.push([o.x1, o.y1], [o.x2, o.y2]));
  const atOpening = (x, y) => ends.some(([a, b]) => Math.abs(a - x) < 1e-3 && Math.abs(b - y) < 1e-3);
  const WALL_RECTS = WALLS.map(([x1, y1, x2, y2, t]) => {
    const h = t / 2, e1 = atOpening(x1, y1) ? 0 : h, e2 = atOpening(x2, y2) ? 0 : h;
    if (x1 === x2) {
      const lo = y1 < y2 ? [y1, e1] : [y2, e2], hi = y1 < y2 ? [y2, e2] : [y1, e1];
      return { x0: x1 - h, y0: lo[0] - lo[1], x1: x1 + h, y1: hi[0] + hi[1], t };
    }
    const lo = x1 < x2 ? [x1, e1] : [x2, e2], hi = x1 < x2 ? [x2, e2] : [x1, e1];
    return { x0: lo[0] - lo[1], y0: y1 - h, x1: hi[0] + hi[1], y1: y1 + h, t };
  });
  // photo stations: a = view direction (0 = right on the sheet, 90 = down), h = lens height, p = pitch
  const PHOTOS = [
    { n: 1, room: "main", x: 4.2, y: 5.75, a: -76, h: 1.6, p: -10, cap: "نمای کلی از سمت آشپزخانه: تخت، قفسه‌ی جداکننده و کاناپه‌ی L" },
    { n: 2, room: "main", x: 4.75, y: 1.9, a: 152, h: 1.25, p: -8, cap: "از پای تخت: کابینت‌ها چپ، درگاه ورودی پشت قفسه" },
    { n: 3, room: "main", x: 4.75, y: 3.75, a: -95, h: 1.6, p: -18, cap: "تخت دونفره با پنجره و رادیاتور در کنارش" },
    { n: 4, room: "main", x: 4.5, y: 1.05, a: 90, h: 1.3, p: -6, cap: "از روی تخت: قوس ناهارخوری، تلویزیون، قوس آشپزخانه، یخچال و کابینت‌ها" },
    { n: 5, room: "main", x: 4.0, y: 3.95, a: 0, h: 1.25, p: -3, cap: "کاناپه‌ی L و میز جلومبلی کنار دیوار پنجره" },
    { n: 6, room: "main", x: 3.2, y: 1.95, a: 42, h: 1.55, p: -8, cap: "از کنار قفسه: نشیمن، قوس ناهارخوری و تلویزیون" },
    { n: 7, room: "kitchen", x: 4.62, y: 7.35, a: 158, h: 1.55, p: -15, cap: "آشپزخانه‌ی جدا: پکیج گازی، سینک و اجاق، پنجره سمت چپ" },
    { n: 8, room: "nook", x: 5.3, y: 8.55, a: -22, h: 1.6, p: -10, cap: "ناهارخوری: میز ۴ نفره، پنجره‌ی بزرگ و قوس رو به نشیمن" },
    { n: 9, room: "main", x: 3.95, y: 4.7, a: -72, h: 2.2, p: -28, cap: "نمای بالا از تخت، قفسه و کاناپه" },
    { n: 10, room: "main", x: 5.25, y: 1.6, a: 0, h: 1.35, p: 8, cap: "کولر گازی بالای کاناپه و پنجره‌ی کنار تخت" },
    { n: 11, room: "entry", x: 2.55, y: 2.75, a: 180, h: 1.6, p: -5, cap: "راهروی ورودی: در اصلی، آینه‌ی قدی، قفسه‌ی مودم" },
    { n: 12, room: "entry", x: 3.85, y: 2.45, a: 180, h: 1.5, p: -5, cap: "دو درگاه از اتاق اصلی: ورودی سمت چپ، حمام با دوش سمت راست" },
    // added to cover walls no listing photo shows: AI renders only, no real photo exists from these angles
    { n: 13, room: "kitchen", x: 2.85, y: 7.5, a: 15, h: 1.55, p: -10, ai: true, refs: [7], cap: "آشپزخانه از گوشه‌ی کنار پنجره" },
    { n: 14, room: "nook", x: 6.5, y: 8.5, a: -135, h: 1.55, p: -8, ai: true, refs: [8], cap: "ناهارخوری رو به قوس و آشپزخانه" },
    { n: 15, room: "bath", x: 0.45, y: 0.85, a: 30, h: 1.55, p: -12, ai: true, refs: [12], cap: "حمام از گوشه‌ی دوش" },
    { n: 16, room: "main", x: 3.6, y: 4.45, a: -105, h: 1.55, p: -8, ai: true, refs: [1, 9], cap: "اتاق اصلی از کنار کابینت‌ها رو به قفسه و تخت" },
    { n: 17, room: "main", x: 6.6, y: 5.7, a: 120, h: 1.55, p: -8, ai: true, refs: [6, 4], cap: "دیوار تلویزیون و قوس‌ها از کنار کاناپه" },
    { n: 18, room: "lobby", x: 2.2, y: 1.66, a: 180, h: 1.55, p: -10, ai: true, refs: [12], cap: "حمام از درگاه پیش‌ورودی" },
  ];
  const TOUR_ORDER = [11, 12, 18, 15, 2, 4, 6, 5, 1, 16, 9, 3, 10, 17, 8, 14, 7, 13];
  const fa = (v) => String(v).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]).replace(".", "٫");
  const isAi = (n) => !!(PHOTOS.find((q) => q.n === n) || {}).ai;
  const photoSrc = (n) => isAi(n) ? `renders/r${String(n).padStart(2, "0")}.jpg` : `photos/p${String(n).padStart(2, "0")}.jpg`;
  const renderSrc = (n) => `renders/r${String(n).padStart(2, "0")}.jpg`;
  const roomName = Object.fromEntries(ROOMS.map((r) => [r.id, r.name]));
  return { ROOMS, WALLS, WALL_RECTS, WINDOWS, OPENINGS, PHOTOS, TOUR_ORDER, fa, photoSrc, renderSrc, roomName };
})();
