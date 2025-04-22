from logger import logger
import os

logger.info("started.")
logger.info("importing modules...")

from sentence_transformers import SentenceTransformer
from constants import PARAPHRASE_MINILM_MAX_TOKENS
from text_splitter import split_text_into_chunks

logger.info("loading model...")

# https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

logger.info("model loaded.")

tokenizer = model.tokenizer


def tokenize(s: str):
    return tokenizer.encode(
        s, add_special_tokens=True, truncation=True, max_length=1000000000
    )


def load_texts():
    for i in range(1, 7):
        with open(f"./assets/texts/{str(i).zfill(8)}.txt", "r", encoding="utf-8") as f:
            yield f.read()


def load_journey_to_the_west():
    dirname = "./assets/journey-to-the-west/"
    files = os.listdir(dirname)

    for file in files:
        with open(f"{dirname}{file}", "r", encoding="utf-8") as f:
            print("read:", file)
            yield f.read()


def text_to_embeddings(text: str):
    return [
        (index, chunk, model.encode(chunk))
        for (index, chunk) in split_text_into_chunks(
            text, tokenizer, PARAPHRASE_MINILM_MAX_TOKENS
        )
    ]


def main():
    min_token = 1000
    i = 0
    # for sentence in load_texts():
    for sentence in load_journey_to_the_west():
        i += 1
        print(f"loaded file ({i})", type(sentence), len(sentence))
        chunks = text_to_embeddings(sentence)
        print(f"splitted file ({i})")
        for index, chunk, embedding in chunks:
            token_count = len(tokenize(chunk))
            print(f"({index},{token_count})", end="")
            print("segment:", chunk)
            if token_count < min_token:
                min_token = token_count
                print("min_token:", min_token)
        print("total segment:", len(chunks))
        print("---")
    print("min_token:", min_token)


if __name__ == "__main__":
    main()
