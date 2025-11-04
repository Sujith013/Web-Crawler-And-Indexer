"""
Respects robots.txt via urllib.robotparser
Accepts an upper bound on total files to download as specified
"""

import os
import re
import PyPDF2
import argparse
import urllib.request
from urllib import robotparser
from indexer import InvertedIndex
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin, urldefrag

#HTML parser to extract text and links
class HtmlParser(HTMLParser):
    def __init__(self, url):
        super().__init__()
        self.text_chunks = []
        self.links = []
        self.url = url

    def handle_data(self, data):
        if data and data.strip():
            self.text_chunks.append(data.strip())

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            href = None
            for (k, v) in attrs:
                if k.lower() == 'href':
                    href = v
                    break
            if href:
                joined = urljoin(self.url, href)
                clean, _ = urldefrag(joined)
                self.links.append(clean)

    def get_text(self):
        return ' '.join(self.text_chunks)

    def get_links(self):
        return list(set(self.links))


class Crawler:
    def __init__(self, url="https://spectrum.library.concordia.ca/", max_docs=50, storage_dir='./data'):
        self.url = url
        self.max_docs = int(max_docs)
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

        parsed = urlparse(url)
        self.url_domain = parsed.netloc
        self.scheme = parsed.scheme

        # robots parser
        self.rp = robotparser.RobotFileParser()
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            self.rp.set_url(robots_url)
            self.rp.read()
        except Exception:
            pass

        self.visited = set()
        self.to_visit = [url]
        self.docs = {}  # doc_id -> {url, type, path}
        self.doc_id_seq = 0

    def allowed(self, url):
        try:
            return self.rp.can_fetch('*', url)
        except Exception:
            return True

    def same_domain(self, url):
        p = urlparse(url)
        return p.netloc == self.url_domain

    def fetch(self, url):
        p = urlparse(url)
        if p.scheme in ('http', 'https'):
            req = urllib.request.Request(url, headers={'User-Agent': 'IR-Crawler/1.0 (+https://example.com)'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                content_type = resp.headers.get('Content-Type', '')
                data = resp.read()
                return content_type, data
        elif p.scheme == 'file' or p.scheme == '':
            # local file
            path = p.path
            if os.name == 'nt' and path.startswith('/') and ':' in path:
                # file:///C:/path -> /C:/path, strip leading /
                path = path.lstrip('/')
            with open(path, 'rb') as f:
                data = f.read()
            # naive content type by extension
            ext = os.path.splitext(path)[1].lower()
            ctype = 'application/octet-stream'
            if ext == '.html' or ext == '.htm':
                ctype = 'text/html'
            elif ext == '.pdf':
                ctype = 'application/pdf'
            return ctype, data
        else:
            raise ValueError(f'Unsupported URL scheme: {p.scheme}')

    def extract_from_html(self, url, data):
        try:
            text = data.decode('utf-8', errors='replace')
        except Exception:
            text = data.decode('latin1', errors='replace')
        parser = HtmlParser(url=url)
        parser.feed(text)
        return parser.get_text(), parser.get_links()

    def save_bin(self, url, data, ext):
        fname = f"doc_{self.doc_id_seq}{ext}"
        path = os.path.join(self.storage_dir, fname)
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def crawl(self, indexer):
        while self.to_visit and len(self.docs) < self.max_docs:
            url = self.to_visit.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)

            if not self.same_domain(url):
                continue
            if not self.allowed(url):
                # respect robots
                print(f"robots skipping {url}")
                continue

            print(f"fetching {url}")
            try:
                ctype, data = self.fetch(url)
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                continue

            doc_type = 'html' if 'html' in ctype else ('pdf' if 'pdf' in ctype else 'binary')
            doc_path = None
            tokens = []
            outlinks = []

            if doc_type == 'html':
                text, links = self.extract_from_html(url, data)
                tokens = re.findall(r"\w+", text.lower())
                outlinks = links
            elif doc_type == 'pdf':
                path = self.save_bin(url, data, '.pdf')
                doc_path = path
                try:
                    with open(path, 'rb') as fh:
                        reader = PyPDF2.PdfReader(fh)
                        text_parts = []
                        for page in reader.pages:
                            try:
                                text_parts.append(page.extract_text() or '')
                            except Exception:
                                pass
                        text = '\n'.join(text_parts)
                        tokens = re.findall(r"\w+", text.lower())
                except Exception:
                    pass

            doc_id = f"{self.doc_id_seq}"
            self.doc_id_seq += 1
            self.docs[doc_id] = {'url': url, 'type': doc_type}
            if doc_path:
                self.docs[doc_id]['path'] = doc_path

            if tokens:
                indexer.add_document(doc_id, tokens)

            for link in outlinks:
                if link not in self.visited and self.same_domain(link):
                    self.to_visit.append(link)

        return self.docs


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--url')
    p.add_argument('--max')
    args = p.parse_args()

    if not args.url:
        args.url="https://spectrum.library.concordia.ca/"
    if not args.max:
        args.max = 50

    idx = InvertedIndex()
    crawler = Crawler(args.url, max_docs=args.max, storage_dir="./data")
    docs = crawler.crawl(indexer=idx)

    for doc_id, meta in docs.items():
        if doc_id in idx.docs:
            idx.docs[doc_id].update(meta)
        else:
            idx.docs[doc_id] = meta
    
    idx.save()

    print(f"Saved index to ./index.json with {len(idx.postings)} tokens and {len(idx.docs)} docs")
