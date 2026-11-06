 import tiktoken

# Your sample text (at least 2 KB: mix of code and normal text)
sample_text = """
def calculate_area(radius):
    if radius < 0:
        return 0
    pi = 3.14159
    return pi * radius * radius

# Some normal text paragraphs below
Tokenization is a fundamental step in language processing and compilers. 
It converts a raw stream of characters into structured tokens like keywords, identifiers, and numbers.
OpenAI's tiktoken uses Byte-Pair Encoding to handle massive vocabularies efficiently.
"""

# Run tiktoken
enc = tiktoken.get_encoding("cl100k_base")
tokens = enc.encode(sample_text)

print(f"Total tiktoken tokens: {len(tokens)}")
