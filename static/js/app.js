(() => {
  'use strict';
  const projects = JSON.parse(document.getElementById('project-data').textContent);
  const projectMap = new Map(projects.map(p => [p.slug, p]));
  const track = document.getElementById('panel-track');
  const grid = document.getElementById('project-grid');
  const search = document.getElementById('search');
  const clearSearch = document.getElementById('clear-search');
  const categoryButtons = [...document.querySelectorAll('.category[data-category]')];
  const cards = [...document.querySelectorAll('.project-card')];
  const utilityCards = [...document.querySelectorAll('.utility-card')];
  const count = document.getElementById('total-count');
  const emptyState = document.getElementById('empty-state');
  const dialog = document.getElementById('project-dialog');
  const releaseList = document.getElementById('release-list');
  const toast = document.getElementById('toast');
  let activePanel = 'catalog';
  let activeCategory = 'Tümü';
  let activeProject = null;
  let toastTimer = null;

  function announce(text) {
    toast.textContent = text;
    toast.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 2400);
  }

  function switchPanel(which) {
    if (which !== 'catalog' && which !== 'studio') return;
    const changed = which !== activePanel;
    if (changed && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      track.classList.add('is-transitioning');
    }
    activePanel = which;
    track.classList.toggle('studio-active', which === 'studio');
    document.getElementById('catalog-panel').inert = which !== 'catalog';
    document.getElementById('studio-panel').inert = which !== 'studio';
    document.querySelectorAll('[data-switch]').forEach(btn => {
      btn.classList.toggle('is-active', btn.dataset.switch === which && btn.classList.contains('segment-btn'));
      if (btn.classList.contains('page-dot')) btn.classList.toggle('on', btn.dataset.switch === which);
    });
    document.getElementById('rail-catalog').classList.toggle('selected', which === 'catalog');
    document.getElementById('rail-studio').classList.toggle('selected', which === 'studio');
    document.getElementById('page-current').textContent = which === 'catalog' ? '01 / 02' : '02 / 02';
    window.history.replaceState(null, '', which === 'studio' ? '#studio' : location.pathname + location.search);
  }


  // Search input can fire repeatedly during IME composition. Coalesce DOM
  // writes into the next frame without running an animation loop at rest.
  let pendingSearchFrame = 0;
  function scheduleFilter() {
    if (pendingSearchFrame) cancelAnimationFrame(pendingSearchFrame);
    pendingSearchFrame = requestAnimationFrame(() => {
      pendingSearchFrame = 0;
      filterCards();
    });
  }

  function filterCards() {
    const keyword = search.value.trim().toLocaleLowerCase('tr-TR');
    let shown = 0;
    cards.forEach(card => {
      const matchesCategory = activeCategory === 'Tümü' || card.dataset.category === activeCategory;
      const matchesKeyword = !keyword || card.dataset.search.toLocaleLowerCase('tr-TR').includes(keyword);
      const visible = matchesCategory && matchesKeyword;
      card.hidden = !visible;
      if (visible) shown++;
    });
    utilityCards.forEach(card => { card.hidden = Boolean(keyword) || activeCategory !== 'Tümü'; });
    count.textContent = `${shown} yazılım`;
    emptyState.hidden = shown > 0;
    grid.hidden = shown === 0;
    clearSearch.hidden = !search.value;
    document.getElementById('collection-scroll').scrollTop = 0;
  }

  function chooseCategory(category) {
    activeCategory = category;
    categoryButtons.forEach(btn => {
      const selected = btn.dataset.category === category;
      btn.classList.toggle('active', selected);
      btn.setAttribute('aria-pressed', String(selected));
    });
    switchPanel('catalog');
    filterCards();
  }

  function resetFilters() {
    search.value = '';
    chooseCategory('Tümü');
    filterCards();
  }

  function el(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  }

  function openProject(slug) {
    const project = projectMap.get(slug);
    if (!project) return;
    activeProject = project;
    document.getElementById('dialog-category').textContent = project.category.toLocaleUpperCase('tr-TR');
    document.getElementById('dialog-icon').textContent = project.icon;
    document.getElementById('dialog-title').textContent = project.name;
    document.getElementById('dialog-platform').textContent = `${project.platform} · Kapalı kaynak yazılım`;
    document.getElementById('dialog-description').textContent = project.description;
    const cover = document.getElementById('dialog-cover');
    cover.hidden = !project.cover;
    if (project.cover) document.getElementById('cover-image').src = project.cover;
    document.getElementById('release-count').textContent = `${project.releases.length} sürüm`;
    releaseList.replaceChildren();
    if (!project.releases.length) {
      const note = el('div', 'unreleased', 'Bu yazılım için henüz indirme dosyası yayınlanmadı. Yeni sürüm eklendiğinde burada görünecek.');
      releaseList.appendChild(note);
    } else {
      project.releases.forEach(release => {
        const entry = el('article', 'release-entry');
        const info = el('div', 'meta');
        info.appendChild(el('strong', '', `Sürüm ${release.version}`));
        info.appendChild(el('small', '', `Windows uygulaması${release.created_at ? ' · ' + release.created_at.slice(0, 10) : ''}`));
        if (release.notes) info.appendChild(el('p', '', release.notes));
        const link = el('a', 'pill-button primary liquid-button', '↓ İndir');
        link.href = release.download_url;
        link.setAttribute('download', '');
        link.setAttribute('aria-label', `${project.name} ${release.version} sürümünü indir`);
        entry.append(info, link);
        releaseList.appendChild(entry);
      });
    }
    if (!dialog.open) dialog.showModal();
    window.history.replaceState(null, '', `#${project.slug}`);
  }

  function formatSize(bytes) {
    if (!Number.isFinite(bytes)) return 'Dosya';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
    return `${(bytes / 1073741824).toFixed(2)} GB`;
  }

  function closeProject() {
    if (dialog.open) dialog.close();
    activeProject = null;
    window.history.replaceState(null, '', activePanel === 'studio' ? '#studio' : location.pathname + location.search);
  }

  async function copyLink() {
    if (!activeProject) return;
    const url = `${location.origin}${location.pathname}#${activeProject.slug}`;
    try {
      await navigator.clipboard.writeText(url);
      announce('Proje bağlantısı kopyalandı');
    } catch (_) {
      const input = document.createElement('textarea');
      input.value = url;
      document.body.appendChild(input);
      input.select();
      const copied = document.execCommand('copy');
      input.remove();
      announce(copied ? 'Proje bağlantısı kopyalandı' : 'Bağlantı kopyalanamadı');
    }
  }

  track.addEventListener('transitionend', event => {
    if (event.target === track && event.propertyName === 'transform') {
      track.classList.remove('is-transitioning');
    }
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) track.classList.remove('is-transitioning');
  });

  cards.forEach(card => card.addEventListener('click', () => openProject(card.dataset.slug)));
  categoryButtons.forEach(btn => btn.addEventListener('click', () => chooseCategory(btn.dataset.category)));
  search.addEventListener('input', scheduleFilter);
  clearSearch.addEventListener('click', () => { search.value = ''; filterCards(); search.focus(); });
  document.getElementById('reset-filters').addEventListener('click', resetFilters);
  document.querySelectorAll('[data-switch]').forEach(btn => btn.addEventListener('click', () => switchPanel(btn.dataset.switch)));
  document.querySelectorAll('[data-prev]').forEach(btn => btn.addEventListener('click', () => switchPanel(activePanel === 'catalog' ? 'studio' : 'catalog')));
  document.querySelectorAll('[data-next]').forEach(btn => btn.addEventListener('click', () => switchPanel(activePanel === 'catalog' ? 'studio' : 'catalog')));
  document.getElementById('studio-card').addEventListener('click', () => switchPanel('studio'));
  document.getElementById('share-card').addEventListener('click', async () => {
    const url = `${location.origin}${location.pathname}`;
    try { await navigator.clipboard.writeText(url); announce('Site bağlantısı kopyalandı'); }
    catch (_) {
      const input = document.createElement('textarea'); input.value = url; document.body.appendChild(input);
      input.select(); const success = document.execCommand('copy'); input.remove();
      announce(success ? 'Site bağlantısı kopyalandı' : 'Bağlantı kopyalanamadı');
    }
  });
  document.getElementById('rail-catalog').addEventListener('click', () => switchPanel('catalog'));
  document.getElementById('rail-studio').addEventListener('click', () => switchPanel('studio'));
  document.getElementById('rail-search').addEventListener('click', () => { switchPanel('catalog'); search.focus(); });
  document.getElementById('go-home').addEventListener('click', () => {resetFilters();switchPanel('catalog');announce('Koleksiyon ana sayfası');});
  document.getElementById('about-shortcut').addEventListener('click', () => switchPanel('studio'));
  document.getElementById('close-dialog').addEventListener('click', closeProject);
  document.getElementById('dialog-done').addEventListener('click', closeProject);
  document.getElementById('copy-project-link').addEventListener('click', copyLink);
  dialog.addEventListener('click', evt => { if (evt.target === dialog) closeProject(); });
  dialog.addEventListener('close', () => { activeProject = null; });
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const next = document.body.dataset.theme === 'lagoon' ? 'pearl' : 'lagoon';
    document.body.dataset.theme = next;
    try { localStorage.setItem('dilekciler-theme', next); } catch (_) { /* private browsing */ }
    announce(next === 'lagoon' ? 'Lagün görünümü' : 'İnci görünümü');
  });

  let touchStartX = 0;
  let touchStartY = 0;
  const workspace = document.getElementById('workspace');
  workspace.addEventListener('touchstart', evt => {
    if (evt.touches.length !== 1) return;
    touchStartX = evt.touches[0].clientX;
    touchStartY = evt.touches[0].clientY;
  }, {passive: true});
  workspace.addEventListener('touchend', evt => {
    const touch = evt.changedTouches[0];
    if (!touch) return;
    const dx = touch.clientX - touchStartX;
    const dy = touch.clientY - touchStartY;
    if (Math.abs(dx) > 75 && Math.abs(dx) > Math.abs(dy) * 1.6 && !evt.target.closest('.categories, .project-card, .search-wrap')) {
      switchPanel(dx < 0 ? 'studio' : 'catalog');
    }
  }, {passive: true});

  document.addEventListener('keydown', evt => {
    if (evt.key === '/' && !dialog.open && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
      evt.preventDefault(); switchPanel('catalog'); search.focus();
    } else if (evt.key === 'Escape' && dialog.open) {
      closeProject();
    } else if (!dialog.open && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName) && evt.key === 'ArrowRight') {
      switchPanel('studio');
    } else if (!dialog.open && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName) && evt.key === 'ArrowLeft') {
      switchPanel('catalog');
    }
  });

  try {document.body.dataset.theme = localStorage.getItem('dilekciler-theme') === 'pearl' ? 'pearl' : 'lagoon';} catch (_) { /* private browsing */ }
  const initialHash = decodeURIComponent(location.hash.slice(1));
  if (initialHash === 'studio') switchPanel('studio');
  else if (projectMap.has(initialHash)) openProject(initialHash);
  filterCards();
})();
