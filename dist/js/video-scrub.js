/**
 * video-scrub.js — Scroll-driven video scrubbing (Nanobanana transition videos)
 *
 * Maps scroll position within a sticky container to video.currentTime.
 * Encoding requirement: high keyframe density (every 1-2 frames) for smooth scrub.
 * Fallback: if video fails to load, container retains static poster image.
 *
 * HTML structure required:
 *   <section class="video-scrub-zone" data-video-scrub>
 *     <div class="video-scrub-zone__sticky">
 *       <video class="video-scrub-zone__video" src="..." muted playsinline preload="auto"></video>
 *     </div>
 *   </section>
 *
 * The section height controls how many pixels of scroll = full video duration.
 * Set height in CSS: e.g. height: 300vh for a leisurely scrub.
 */

(function () {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const zones = document.querySelectorAll('[data-video-scrub]');

  if (!zones.length || prefersReduced) return;

  zones.forEach((zone) => {
    const video = zone.querySelector('.video-scrub-zone__video');
    if (!video) return;

    // Pause on load — user scroll drives playback, not autoplay
    video.pause();
    video.currentTime = 0;

    let rafId = null;

    const update = () => {
      const rect = zone.getBoundingClientRect();
      const zoneHeight = zone.offsetHeight;
      const viewportHeight = window.innerHeight;

      // scrolled = how far the zone top has scrolled above viewport top
      // 0 when zone top enters bottom of viewport
      // 1 when zone bottom exits top of viewport
      const scrolled = -rect.top / (zoneHeight - viewportHeight);
      const progress = Math.min(1, Math.max(0, scrolled));

      if (video.readyState >= 2 && video.duration) {
        video.currentTime = progress * video.duration;
      }

      rafId = null;
    };

    window.addEventListener('scroll', () => {
      if (rafId) return;
      rafId = requestAnimationFrame(update);
    }, { passive: true });

    // Initial position
    update();
  });
})();
