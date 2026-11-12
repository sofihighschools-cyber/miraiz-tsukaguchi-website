(() => {
  'use strict';

  const grid = document.getElementById('news-grid');
  const status = document.getElementById('news-status');
  const filters = Array.from(document.querySelectorAll('.news-filter'));
  if (!grid || !status) return;

  const escapeHtml = (value = '') => String(value).replace(/[&<>"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'
  }[char]));

  const isAllowedUrl = (value, image = false) => {
    try {
      const url = new URL(value);
      if (url.protocol !== 'https:') return false;
      const allowed = image
        ? ['assets.st-note.com', 'prcdn.freetls.fastly.net', 'prtimes.jp']
        : ['note.com', 'prtimes.jp'];
      return allowed.some((host) => url.hostname === host || url.hostname.endsWith(`.${host}`));
    } catch (_) {
      return false;
    }
  };

  const formatDate = (value) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat('ja-JP', {
      timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(date);
  };

  const cardHtml = (item) => {
    const source = item.source === 'prtimes' ? 'prtimes' : 'note';
    const sourceLabel = source === 'prtimes' ? 'PR TIMES' : 'note';
    const href = isAllowedUrl(item.url) ? item.url : '#';
    const image = isAllowedUrl(item.image, true)
      ? `<img src="${escapeHtml(item.image)}" alt="" loading="lazy" width="800" height="450">`
      : '<span class="news-card__placeholder"><img src="assets/img/logo-miraiz.png" alt=""></span>';
    return `
      <article class="news-card" data-source="${source}">
        <a class="news-card__link" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">
          <div class="news-card__media">
            ${image}
            <span class="news-card__source news-card__source--${source}">${sourceLabel}</span>
          </div>
          <div class="news-card__body">
            <time datetime="${escapeHtml(item.published)}">${formatDate(item.published)}</time>
            <h3>${escapeHtml(item.title)}</h3>
            ${item.description ? `<p class="news-card__description">${escapeHtml(item.description)}</p>` : ''}
            <span class="news-card__more">記事を読む <span aria-hidden="true">↗</span></span>
          </div>
        </a>
      </article>`;
  };

  const applyFilter = (filter) => {
    let visible = 0;
    document.querySelectorAll('.news-card').forEach((card) => {
      const show = filter === 'all' || card.dataset.source === filter;
      card.hidden = !show;
      if (show) visible += 1;
    });
    const empty = grid.querySelector('.news-empty');
    if (empty) empty.remove();
    if (!visible) grid.insertAdjacentHTML('beforeend', '<p class="news-empty">該当するお知らせはまだありません。</p>');
  };

  filters.forEach((button) => {
    button.addEventListener('click', () => {
      filters.forEach((item) => {
        const active = item === button;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-pressed', String(active));
      });
      applyFilter(button.dataset.filter);
    });
  });

  fetch('data/news.json', { cache: 'no-cache' })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      const items = Array.isArray(data.items) ? data.items : [];
      grid.innerHTML = items.map(cardHtml).join('');
      if (!items.length) grid.innerHTML = '<p class="news-empty">お知らせはまだありません。</p>';
      const synced = data.updated_at ? formatDate(data.updated_at) : '';
      status.textContent = synced ? `note・PR TIMESから自動連携（最終データ更新：${synced}）` : '';
    })
    .catch(() => {
      status.className = 'news-status is-error';
      status.textContent = 'お知らせを読み込めませんでした。時間をおいて再度お試しください。';
    });
})();
