document.querySelectorAll('.post-body pre').forEach((pre) => {
    pre.setAttribute('tabindex', '0');
    pre.setAttribute('role', 'region');
    pre.setAttribute('aria-label', 'Code block');
});
