const topButton = document.querySelector('.scroll-top');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
if (topButton) {
    const updateButton = () => { topButton.hidden = window.scrollY < 500; };
    window.addEventListener('scroll', updateButton, { passive: true });
    updateButton();
    topButton.addEventListener('click', () => {
        document.querySelector('.site-title')?.focus({ preventScroll: true });
        window.scrollTo({ top: 0, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    });
}
document.querySelectorAll('.post-body pre').forEach((pre) => {
    pre.setAttribute('tabindex', '0');
    pre.setAttribute('role', 'region');
    pre.setAttribute('aria-label', 'Code block');
});
