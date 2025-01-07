import markdown
import os

md = markdown.Markdown(extensions=['meta', 'mdx_math', 'extra'], enable_dollar_delimiter=True)

# create blog directory if it doesn't exist
os.makedirs("blog", exist_ok=True)

with open("templates/post.html", "r") as file:
    post_template = file.read()

with open("templates/homepage.html", "r") as file:
    homepage_template = file.read()

blog_posts = os.listdir("posts")

post_bullets = []

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

    if not draft:
        post_bullets.append((date, f"<li><a href='blog/{post}'>{title}</a> [{date}]</li>"))

post_bullets.sort(key=lambda x: x[0], reverse=True)
posts_html = "\n".join([post_bullet for _, post_bullet in post_bullets])

homepage_html = homepage_template.format(posts=posts_html)

with open("index.html", "w") as file:
    file.write(homepage_html)
