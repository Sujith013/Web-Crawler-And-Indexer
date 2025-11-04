import json
from collections import defaultdict, Counter

class InvertedIndex:
    def __init__(self):
        self.postings = defaultdict(dict)
        self.docs = {}

    def add_document(self, doc_id, tokens, metadata=None):
        freq = Counter(tokens)
        for tok, cnt in freq.items():
            self.postings[tok][doc_id] = cnt
        if metadata is None:
            metadata = {}
        self.docs[doc_id] = metadata

    def save(self, filepath="./index.json"):
        out = {'postings': {}, 'docs': self.docs}
        for tok, m in self.postings.items():
            out['postings'][tok] = m
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    def load(self, filepath="./index.json"):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.postings = {k: v for k, v in data.get('postings', {}).items()}
        self.docs = data.get('docs', {})

    def get_postings(self, token):
        return self.postings.get(token, {})

if __name__ == '__main__':
    index = InvertedIndex()
    index.load("./index.json")

    while True:
        query = input("Enter a token to search (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        postings = index.get_postings(query)
        if postings:
            print(f"Token '{query}' found in documents:")
            for doc_id, freq in postings.items():
                print(f"  Document ID: {doc_id}, Frequency: {freq}")
        else:
            print(f"Token '{query}' not found in any document.")
