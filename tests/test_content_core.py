import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from content_core import read_article,render_markdown,strip_leading_h1
class Tests(unittest.TestCase):
    def test_frontmatter(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'sample.md'; p.write_text('---\ntitle: "示例"\ncontent_id: fixed-id\n---\n\n# 示例\n\n正文',encoding='utf-8')
            a=read_article(p); self.assertEqual(a.title,'示例'); self.assertEqual(a.content_id,'fixed-id'); self.assertNotIn('# 示例',strip_leading_h1(a.body))
    def test_render(self):
        md='''## 小标题\n\n**加粗**和`代码`\n\n> 引用\n\n1. 第一项\n2. 第二项\n\n| 工具 | 价格 |\n|---|---|\n| A | 免费 |\n\n![图](/images/a.jpg)'''
        h=render_markdown(md,lambda s:'resolved:'+s,first_paragraph_track=True)
        for expected in ('<strong>加粗</strong>','<code>代码</code>','<blockquote style=','<ol>','<table style=','resolved:/images/a.jpg'): self.assertIn(expected,h)
        self.assertNotIn('**',h); self.assertNotIn('|---|',h)
if __name__=='__main__': unittest.main()
