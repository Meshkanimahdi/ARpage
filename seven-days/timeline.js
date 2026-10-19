(function (root) {
  const BPM = 90, BEAT = 60 / BPM, BAR = BEAT * 4;
  const T = (bar, beat = 0) => +((bar * 4 + beat) * BEAT).toFixed(4);
  const DURATION = T(46);
  const SCENES = {
    s0: [T(0), T(2)], s1: [T(2), T(5)], s2: [T(5), T(6)], s3: [T(6), T(10)],
    s4: [T(10), T(13)], s5: [T(13), T(19)], s6: [T(19), T(24)], s7: [T(24), T(29)],
    s8: [T(29), T(34)], s9: [T(34), T(40)], s10: [T(40), T(43)], s11: [T(43), T(46)]
  };
  const NO_TIMES = [];
  (function () { let b = 24 * 4 + 2, step = 1; while (b < 26 * 4 + 3) { NO_TIMES.push(+(b * BEAT).toFixed(4)); b += step; step = Math.max(0.25, step * 0.82); } })();
  const M = {
    introName: T(0, 0.5), introPresents: T(1, 0), introOut: T(1, 3),
    phoneIn: T(2, 0), ding1: T(2, 2), rewind: T(4, 1),
    drop: T(5, 0), hudIn: T(5, 3),
    d0In: T(6, 0), bell: T(7, 3), d0Out: T(9, 3.5),
    epic: T(10, 0), rocket: T(10, 2), scratch: T(11, 0), scribble: T(11, 1.25), crumple: T(11, 3), restart: T(12, 0), coin1: T(12, 3),
    d1: T(13, 0), d2: T(15, 0), shrug: T(15, 1), good: T(16, 1), howMuch: T(17, 0), zoom: T(17, 3),
    d3: T(19, 0), swipe: T(20, 0), paper: T(21, 0), tape1: T(21, 0.5), tape2: T(21, 1), write: T(21, 1.5), costStamp: T(23, 0),
    d4: T(24, 0), deadStop: T(26, 3), d5: T(27, 0), okay: T(27, 1), beatBack: T(28, 0),
    d6: T(29, 0), ding2: T(29, 2), count: T(30, 0), coin2: T(31, 0), wallet: T(33, 1.5),
    d7: T(34, 0), grid: T(37, 0),
    cube: T(40, 0), steps: [T(40, 1), T(40, 3), T(41, 1), T(41, 3)], gold: T(42, 0),
    end1: T(43, 0), end2: T(43, 1), end3: T(43, 2), endInfo: T(43, 3), endTag: T(44, 2)
  };
  root.TL = { BPM, BEAT, BAR, T, DURATION, SCENES, M, NO_TIMES };
  if (typeof module !== 'undefined') module.exports = root.TL;
})(typeof window !== 'undefined' ? window : globalThis);
