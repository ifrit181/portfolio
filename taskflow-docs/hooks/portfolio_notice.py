NOTICE = (
    '!!! warning "Портфолио"\n'
    '    Содержимое вымышленное. Сайт создан как демонстрация навыков\n'
    '    технического писателя. Продукты, компании и данные не существуют.\n'
)
# это список страниц, если добавлять не везде
#EXCLUDE = {"index.md", "installation.md", "faq.md", "quick-start.md", "glossary.md", "interface.md", "tasks.md", "projects.md", "reports.md", "users.md"}

#def on_page_markdown(markdown, page, config, files):
#    if page.file.src_path in EXCLUDE:
#        return markdown
#    return NOTICE + "\n" + markdown

def on_page_markdown(markdown, page, config, files):
    """MkDocs вызывает эту функцию для каждой страницы при сборке."""
    return NOTICE + "\n" + markdown