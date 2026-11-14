#!/usr/bin/env python3
"""Render cached feed cards into public HTML; no network or credentials required."""
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def safe_url(value, hosts):
    parsed = urlparse(value or '')
    return value if parsed.scheme == 'https' and parsed.hostname in hosts else ''


def card(item, compact=False):
    source = item['source']
    label = {'note': 'Note', 'prtimes': 'PR TIMES'}[source]
    url = safe_url(item['url'], ('note.com', 'prtimes.jp'))
    if not url:
        raise ValueError('Invalid article URL')
    e = html.escape
    image = safe_url(item.get('image'), ('assets.st-note.com', 'prcdn.freetls.fastly.net', 'prtimes.jp'))
    media = (f'<img src="{e(image)}" alt="" loading="lazy" width="800" height="450">'
             if image else '<span class="news-card__placeholder"><img src="assets/img/logo-miraiz.png" alt=""></span>')
    date = datetime.fromisoformat(item['published']).astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y/%m/%d')
    description = (f'<p class="news-card__description">{e(item["description"])}</p>'
                   if item.get('description') and not compact else '')
    return f'''<article class="news-card" data-source="{source}">
  <a class="news-card__link" href="{e(url)}" target="_blank" rel="noopener noreferrer">
    <div class="news-card__media">{media}<span class="news-card__source news-card__source--{source}">{label}</span></div>
    <div class="news-card__body"><time datetime="{e(item['published'])}">{date}</time>
      <h3>{e(item['title'])}</h3>{description}
      <span class="news-card__more">記事を読む <span aria-hidden="true">↗</span></span>
    </div>
  </a>
</article>'''


def render(root=ROOT):
    data = json.loads((root / 'data/news.json').read_text(encoding='utf-8'))
    items = sorted(data['items'], key=lambda x: datetime.fromisoformat(x['published']), reverse=True)
    if not items:
        raise ValueError('Refusing to render an empty feed')
    for filename, limit in [('index.html', 3), ('news.html', None)]:
        path = root / filename
        page = path.read_text(encoding='utf-8')
        cards = '\n'.join(card(item, compact=bool(limit)) for item in items[:limit])
        page, count = re.subn(r'(<!-- news-cards:start -->).*?(<!-- news-cards:end -->)',
                             lambda m: m[1] + '\n' + cards + '\n' + m[2], page, flags=re.S)
        if count != 1:
            raise ValueError(f'{filename}: expected one card region')
        if page != path.read_text(encoding='utf-8'):
            path.write_text(page, encoding='utf-8')
        print(f'{filename}: {len(items[:limit])} cards')


if __name__ == '__main__':
    render()
