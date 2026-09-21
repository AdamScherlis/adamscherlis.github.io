import markdown
import os
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

SITE_URL = "https://adam.scherl.is"
SITE_TITLE = "Adam Scherlis"

md = markdown.Markdown(extensions=['meta', 'mdx_math', 'extra'], enable_dollar_delimiter=True)

# create blog directory if it doesn't exist
os.makedirs("blog", exist_ok=True)

with open("templates/post.html", "r") as file:
    post_template = file.read()

with open("templates/homepage.html", "r") as file:
    homepage_template = file.read()

blog_posts = os.listdir("posts")

post_bullets = []
feed_items = []

for post in blog_posts:
    with open(f"posts/{post}/index.md", "r") as file:
        content = file.read()

    content_html = md.convert(content)
    title = md.Meta.get('title', [None])[0]
    date = md.Meta.get('date', [None])[0]
    draft = md.Meta.get('draft', [False])[0]

    if draft and draft != "secret":
        continue

    post_html = post_template.format(title=title, date=date, content=content_html)

    # create new-blog directory if it doesn't exist
    os.makedirs(f"blog/{post}", exist_ok=True)

    with open(f"blog/{post}/index.html", "w") as file:
        file.write(post_html)

    if not draft or draft.lower() == "false":
        post_bullets.append((date, f"<li><a href='blog/{post}'>{title}</a> [{date}]</li>"))
        feed_items.append((date, post, title, content_html))

post_bullets.sort(key=lambda x: x[0], reverse=True)
posts_html = "\n".join([post_bullet for _, post_bullet in post_bullets])

homepage_html = homepage_template.format(posts=posts_html)

with open("index.html", "w") as file:
    file.write(homepage_html)


# RSS feed

def absolutize(html):
    """Rewrite the relative URLs used in post pages to absolute ones."""
    html = re.sub(r'(src|href)="\.\./\.\./', rf'\1="{SITE_URL}/', html)
    html = re.sub(r'(src|href)="/', rf'\1="{SITE_URL}/', html)
    return html

def rfc822(date):
    return format_datetime(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc))

feed_items.sort(key=lambda x: x[0], reverse=True)

items_xml = []
for date, post, title, content_html in feed_items:
    url = f"{SITE_URL}/blog/{post}/"
    items_xml.append(f"""    <item>
      <title>{escape(title)}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{rfc822(date)}</pubDate>
      <description><![CDATA[{absolutize(content_html)}]]></description>
    </item>""")

last_build = rfc822(feed_items[0][0]) if feed_items else format_datetime(datetime.now(timezone.utc))

feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{SITE_URL}/</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
    <description>Blog posts by Adam Scherlis</description>
    <language>en</language>
    <lastBuildDate>{last_build}</lastBuildDate>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""

with open("feed.xml", "w") as file:
    file.write(feed_xml)
