/* PPT-Agent Slide Navigation — ported from presentation-as-code (algo-insight) */
/* Zero dependencies, 77 lines */

(function () {
  const slides = document.querySelectorAll('.slide');
  if (!slides.length) return;

  let current = 0;
  const total = slides.length;

  const counter = document.querySelector('.slide-counter');
  const progressFill = document.querySelector('.progress-fill');

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const idx = Array.from(slides).indexOf(entry.target);
          if (idx >= 0) update(idx);
        }
      });
    },
    { threshold: 0.4 }
  );

  slides.forEach((s) => observer.observe(s));

  function update(idx) {
    current = idx;
    if (counter) counter.textContent = `${idx + 1} / ${total}`;
    if (progressFill) progressFill.style.width = `${((idx + 1) / total) * 100}%`;
  }

  function goTo(idx) {
    const target = Math.max(0, Math.min(idx, total - 1));
    slides[target].scrollIntoView({ behavior: 'smooth' });
  }

  document.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
      case ' ':
        e.preventDefault();
        goTo(current + 1);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        goTo(current - 1);
        break;
      case 'Home':
        e.preventDefault();
        goTo(0);
        break;
      case 'End':
        e.preventDefault();
        goTo(total - 1);
        break;
    }
  });

  function setupButtons() {
    document.querySelectorAll('[data-dir]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const dir = parseInt(btn.dataset.dir, 10);
        goTo(current + dir);
      });
    });
  }

  update(0);
  setupButtons();
})();
