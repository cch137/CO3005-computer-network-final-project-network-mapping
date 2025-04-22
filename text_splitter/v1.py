import regex as re
from typing import List, Tuple
import nltk
from functools import lru_cache

# Download sentence segmentation resources
nltk.download("punkt")
nltk.download("punkt_tab")

# Constants for separator weights as a tuple for immutability
WEIGHTS: Tuple[int, int, int, int, int] = (4, 3, 2, 1, 0)
(
    PARAGRAPH_SEPARATOR_WEIGHT,
    SENTENCE_TERMINATOR_WEIGHT,
    OTHER_PUNCTUATION_WEIGHT,
    SPACE_WEIGHT,
    NO_WEIGHT,
) = WEIGHTS


@lru_cache(maxsize=2048)
def get_weight(char: str) -> int:
    """
    Determine the weight of a character based on its type for text splitting.
    Uses LRU cache to avoid repeated regex matching for the same character.

    Weights:
    - 4: Paragraph separators (\n, \r, Zl, Zp)
    - 3: Sentence terminators (STerm)
    - 2: Other punctuation (Po)
    - 1: Spaces (Zs)
    - 0: Other characters

    Args:
        char (str): A single character to evaluate.

    Returns:
        int: The weight of the character.
    """
    if (
        re.match(r"[\n\r]", char)
        or re.match(r"\p{Zl}", char)
        or re.match(r"\p{Zp}", char)
    ):
        return PARAGRAPH_SEPARATOR_WEIGHT
    elif re.match(r"\p{STerm}", char):
        return SENTENCE_TERMINATOR_WEIGHT
    elif re.match(r"\p{Po}", char):
        return OTHER_PUNCTUATION_WEIGHT
    elif re.match(r"\p{Zs}", char):
        return SPACE_WEIGHT
    else:
        return NO_WEIGHT


def split_text_by_tokens(
    input_string: str, tokenizer, max_tokens: int, start_idx: int = 0
) -> List[Tuple[int, str]]:
    """
    Split the input text into segments with a maximum token count, prioritizing splits at high-weight separators.

    Args:
        input_string (str): The text to be split.
        tokenizer: The tokenizer to count tokens.
        max_tokens (int): The maximum number of tokens per segment.
        start_idx (int): The starting index of the input_string in the original text.

    Returns:
        List[Tuple[int, str]]: A list of tuples containing the starting index and text segment.

    Raises:
        ValueError: If max_tokens is not a positive integer or text cannot be split.
    """
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer.")

    result = []
    remaining = input_string
    current_start_idx = start_idx

    while remaining:
        tokens = tokenizer.encode(
            remaining,
            add_special_tokens=True,
            truncation=True,
            max_length=max_tokens + 1,
        )
        if len(tokens) <= max_tokens:
            result.append((current_start_idx, remaining))
            break

        # Find the best split point within token limit
        best_split_idx = None
        best_weight = -1
        best_token_count = max_tokens + 1

        for i in range(1, len(remaining)):
            substring = remaining[:i]
            current_tokens = tokenizer.encode(
                substring,
                add_special_tokens=True,
                truncation=True,
                max_length=max_tokens + 1,
            )
            token_count = len(current_tokens)

            if token_count <= max_tokens:
                char = remaining[i - 1] if i > 0 else ""
                weight = get_weight(char)
                # Update best split if:
                # - Higher weight, or
                # - Same weight but closer to max_tokens
                if weight > best_weight or (
                    weight == best_weight and token_count > best_token_count
                ):
                    best_weight = weight
                    best_split_idx = i
                    best_token_count = token_count

        if best_split_idx is not None:
            result.append((current_start_idx, remaining[:best_split_idx]))
            current_start_idx += best_split_idx
            remaining = remaining[best_split_idx:]
        else:
            # Fallback to last valid token boundary
            for i in range(len(remaining) - 1, 0, -1):
                substring = remaining[:i]
                if (
                    len(
                        tokenizer.encode(
                            substring,
                            add_special_tokens=True,
                            truncation=True,
                            max_length=max_tokens + 1,
                        )
                    )
                    <= max_tokens
                ):
                    result.append((current_start_idx, substring))
                    current_start_idx += i
                    remaining = remaining[i:]
                    break
            else:
                raise ValueError(
                    "Cannot split text within token limit; consider increasing max_tokens."
                )

    return result


def split_text_into_chunks(
    text: str, tokenizer, max_tokens: int
) -> List[Tuple[int, str]]:
    """
    Split text into chunks using SentenceTransformer tokenizer and weighted separators.
    Returns a list of tuples with the starting index and the chunk text.

    Args:
        text (str): The input text to split.
        tokenizer: The tokenizer to use for token counting.
        max_tokens (int): Maximum number of tokens per chunk.

    Returns:
        List[Tuple[int, str]]: List of tuples containing the starting index and text chunks.
    """
    # Split text into sentences using NLTK
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk_sentences = []
    current_token_count = 0
    current_start_idx = 0

    for sentence in sentences:
        tokens = tokenizer.encode(
            sentence,
            add_special_tokens=True,
            truncation=True,
            max_length=max_tokens + 1,
        )
        token_count = len(tokens)

        if current_token_count + token_count <= max_tokens:
            current_chunk_sentences.append(sentence)
            current_token_count += token_count
        else:
            if current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                # Find the actual start index of the chunk in the original text
                chunk_start_idx = text.find(chunk_text, current_start_idx)
                if chunk_start_idx == -1:
                    chunk_start_idx = current_start_idx
                sub_chunks = split_text_by_tokens(
                    chunk_text, tokenizer, max_tokens, chunk_start_idx
                )
                chunks.extend(sub_chunks)
                current_start_idx = chunk_start_idx + len(chunk_text)
            current_chunk_sentences = [sentence]
            current_token_count = token_count

    # Process the last chunk
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        chunk_start_idx = text.find(chunk_text, current_start_idx)
        if chunk_start_idx == -1:
            chunk_start_idx = current_start_idx
        sub_chunks = split_text_by_tokens(
            chunk_text, tokenizer, max_tokens, chunk_start_idx
        )
        chunks.extend(sub_chunks)

    return chunks
