/**
 * scroll-timeline.js — CSS Scroll Timeline progressive enhancement
 *
 * Activates on browsers that support animation-timeline (Chrome 115+, Safari 18+).
 * Falls back gracefully — IntersectionObserver animations in scroll.js still run.
 *
 * Usage: Include after scroll.js. Elements use classes from scroll-animations.css.
 * HTML convention: data-scroll-anim="fade-up|scale-in|parallax|view-fade"
 */

(function () {
  // Feature detect — animation-timeline support
  const supported = CSS.supports('animation-timeline', 'scroll()');

  if (!supported) return; // scroll.js IntersectionObserver handles fallback

  // Respect reduced motion at the JS level too
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) return;

  // Mark root so CSS can key off support
  document.documentElement.classList.add('scroll-timeline-supported');

  /**
   * Stagger view() entrance animations.
   * Elements in a .stagger-scroll parent get --stagger-delay set.
   * CSS: animation-timeline: view(); animation-delay: var(--stagger-delay);
   */
  document.querySelectorAll('.stagger-scroll').forEach((parent) => {
    [...parent.children].forEach((child, i) => {
      child.style.setProperty('--stagger-delay', `${i * 80}ms`);
    });
  });

  /**
   * Parallax hero image via scroll() on the root.
   * Applies to any element with data-parallax-speed attribute.
   * CSS handles the animation; this only sets --parallax-speed.
   */
  document.querySelectorAll('[data-parallax-speed]').forEach((el) => {
    const speed = parseFloat(el.dataset.parallaxSpeed) || 0.3;
    el.style.setProperty('--parallax-speed', speed);
  });
})();
