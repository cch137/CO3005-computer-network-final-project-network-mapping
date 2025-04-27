from .logger import logger
import os

logger.info("importing modules...")

from typing import List, Tuple, Generator, Any
from sentence_transformers import SentenceTransformer
from constants import PARAPHRASE_MINILM_MAX_TOKENS
from text_splitter import split_text_into_chunks as raw_split_text_into_chunks


logger.info("loading model...")

# https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

logger.info("model loaded.")

tokenizer = model.tokenizer


def load_text_assets(dirname: str):
    files = os.listdir(dirname)

    for file in files:
        with open(f"{dirname}{file}", "r", encoding="utf-8") as f:
            print("read:", file)
            yield f.read()


def split_text_to_chunks(text: str, optimize=True):
    return raw_split_text_into_chunks(
        text, tokenizer, PARAPHRASE_MINILM_MAX_TOKENS, optimize
    )


def text_to_embeddings(
    text: str,
) -> Generator[Tuple[int, str, int, List[float]], Any, None]:
    """
    Convert text into embeddings by splitting it into chunks and encoding each chunk.

    Args:
        text (str): The input text to be converted into embeddings.

    Returns:
        Generator[Tuple[int, str, int, torch.Tensor]]: A list of tuples where each tuple contains:
            - index (int): The index of the chunk start at.
            - chunk (str): The text chunk.
            - token_count (int): The number of tokens in the chunk.
            - embedding (torch.Tensor): The embedding vector for the chunk.
    """
    for index, chunk, token_count in split_text_to_chunks(text):
        yield (
            index,
            chunk,
            token_count,
            model.encode(chunk).tolist(),
        )
