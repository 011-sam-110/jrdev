(function() {
  'use strict';

  /* ── Velocity-scroll testimonials (inspired by Framer Motion parallax) ── */
  (function initVelocityScroll() {
    var track1 = document.querySelector('.home-reviews-track--1');
    var track2 = document.querySelector('.home-reviews-track--2');
    if (!track1 || !track2) return;

    var row2 = track2.closest('.home-reviews-row');
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion && row2) {
      row2.style.display = 'none';
      track1.style.animation = 'home-reviews-marquee 45s linear infinite';
      return;
    }

    track2.innerHTML = track1.innerHTML;

    var track2Initialized = false;

    var BASE_VELOCITY = 50;
    var VELOCITY_MAP = [0, 3];
    var VELOCITY_FACTOR = [0, 5];
    var SMOOTH = 0.12;

    var scrollY = window.scrollY || window.pageYOffset;
    var lastScrollY = scrollY;
    var lastTime = performance.now();
    var rawVelocity = 0;
    var smoothVelocity = 0;
    var pos1 = 0;
    var pos2 = 0;
    var directionFactor = 1;
    var contentWidth1 = 0;
    var contentWidth2 = 0;

    function mapRange(v, inMin, inMax, outMin, outMax) {
      var t = (v - inMin) / (inMax - inMin);
      return outMin + t * (outMax - outMin);
    }

    function clamp(v, min, max) {
      return Math.max(min, Math.min(max, v));
    }

    function measureContentWidth() {
      if (track1 && track1.firstElementChild) {
        var firstHalf = 0;
        var cards = track1.querySelectorAll('.home-review-card');
        var half = Math.floor(cards.length / 2);
        for (var i = 0; i < half; i++) {
          var card = cards[i];
          if (card) firstHalf += card.offsetWidth + 24;
        }
        contentWidth1 = firstHalf;
        contentWidth2 = firstHalf;
      }
    }

    function onScroll() {
      var now = performance.now();
      var newScrollY = window.scrollY || window.pageYOffset;
      var dt = now - lastTime;
      if (dt > 0) {
        rawVelocity = (newScrollY - lastScrollY) / dt;
      }
      lastScrollY = newScrollY;
      lastTime = now;
    }

    function animate(t) {
      var now = performance.now();
      var delta = now - lastTime;
      lastTime = now;

      if (contentWidth1 === 0) measureContentWidth();

      /* Don't move until we have valid dimensions - prevents "running out of cards" */
      if (contentWidth1 > 0) {
        /* Track 2 starts at -contentWidth2 so it scrolls right without revealing empty space */
        if (!track2Initialized) {
          pos2 = -contentWidth2;
          track2Initialized = true;
        }

        smoothVelocity += (rawVelocity - smoothVelocity) * SMOOTH;
        var vf = mapRange(clamp(smoothVelocity, VELOCITY_MAP[0], VELOCITY_MAP[1]), VELOCITY_MAP[0], VELOCITY_MAP[1], VELOCITY_FACTOR[0], VELOCITY_FACTOR[1]);
        if (smoothVelocity < 0) vf = mapRange(clamp(smoothVelocity, -VELOCITY_MAP[1], 0), -VELOCITY_MAP[1], 0, -VELOCITY_FACTOR[1], 0);

        if (vf < 0) directionFactor = -1;
        else if (vf > 0) directionFactor = 1;

        var moveBy = directionFactor * BASE_VELOCITY * (delta / 1000);
        moveBy += directionFactor * moveBy * vf;

        pos1 -= moveBy;
        pos2 += moveBy;

        while (pos1 < -contentWidth1) pos1 += contentWidth1;
        while (pos1 > 0) pos1 -= contentWidth1;
        /* Track 2: keep in [-contentWidth2, 0] for seamless right-scroll loop */
        while (pos2 >= 0) pos2 -= contentWidth2;
        while (pos2 < -contentWidth2) pos2 += contentWidth2;
      }

      track1.style.transform = 'translateX(' + pos1 + 'px)';
      track2.style.transform = 'translateX(' + pos2 + 'px)';

      requestAnimationFrame(animate);
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', measureContentWidth);

    /* Defer start until after layout (helps when reviews section is below the fold) */
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        measureContentWidth();
        requestAnimationFrame(animate);
      });
    });
  })();
})();
