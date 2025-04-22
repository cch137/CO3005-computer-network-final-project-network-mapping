import regex as re
from typing import List, Tuple
from functools import lru_cache

# Separator weight constants
WEIGHTS = (4, 3, 2, 1, 0)
(
    PARAGRAPH_SEPARATOR_WEIGHT,
    SENTENCE_TERMINATOR_WEIGHT,
    OTHER_PUNCTUATION_WEIGHT,
    SPACE_WEIGHT,
    NO_WEIGHT,
) = WEIGHTS


@lru_cache(maxsize=2048)
def get_weight(char: str) -> int:
    """Determine the weight of a character for splitting purposes."""
    if re.match(r"[\n\r]|\p{Zl}|\p{Zp}", char):
        return PARAGRAPH_SEPARATOR_WEIGHT
    elif re.match(r"\p{STerm}", char):
        return SENTENCE_TERMINATOR_WEIGHT
    elif re.match(r"\p{Po}", char):
        return OTHER_PUNCTUATION_WEIGHT
    elif re.match(r"\p{Zs}", char):
        return SPACE_WEIGHT
    return NO_WEIGHT


def split_text_into_chunks(
    text: str, tokenizer, max_tokens: int
) -> List[Tuple[int, str]]:
    """Split text into chunks based on separator weights and token limits, greedily merging chunks.

    Args:
        text: Input text to be split
        tokenizer: Tokenizer object with encode method
        max_tokens: Maximum number of tokens per chunk

    Returns:
        List of tuples containing (start_index, chunk_text)
    """
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer")

    def split_by_weight(
        text: str, weight: int, start_idx: int
    ) -> List[Tuple[int, str, int]]:
        """Recursively split text at the given weight level, tracking token counts."""
        chunks = []
        current_pos = 0
        current_chunk = []
        current_chunk_tokens = 0
        current_chunk_start = start_idx

        i = 0
        while i < len(text):
            char = text[i]
            char_weight = get_weight(char)

            # Consider splitting if we hit a separator of the current weight
            if char_weight >= weight:
                # Try to add the current segment to the chunk
                segment = text[current_pos : i + 1]
                segment_tokens = len(
                    tokenizer.encode(
                        segment,
                        add_special_tokens=True,
                        truncation=True,
                        max_length=max_tokens + 1,
                    )
                )

                if current_chunk_tokens + segment_tokens <= max_tokens:
                    current_chunk.append(segment)
                    current_chunk_tokens += segment_tokens
                    current_pos = i + 1
                else:
                    # If adding this segment exceeds max_tokens, finalize current chunk
                    if current_chunk:
                        chunk_text = "".join(current_chunk)
                        chunks.append(
                            (current_chunk_start, chunk_text, current_chunk_tokens)
                        )
                        current_chunk_start += len(chunk_text)
                        current_chunk = []
                        current_chunk_tokens = 0

                    # If single segment exceeds max_tokens, try lower weight
                    if segment_tokens > max_tokens and weight > NO_WEIGHT:
                        sub_chunks = split_by_weight(
                            segment, weight - 1, current_chunk_start
                        )
                        chunks.extend(sub_chunks)
                        current_chunk_start += len(segment)
                        current_pos = i + 1
                    elif segment_tokens <= max_tokens:
                        current_chunk.append(segment)
                        current_chunk_tokens = segment_tokens
                        current_pos = i + 1
                    else:
                        raise ValueError(
                            "Cannot split segment within token limit; "
                            "consider increasing max_tokens"
                        )

            i += 1

        # Handle remaining text
        if current_pos < len(text):
            remaining = text[current_pos:]
            remaining_tokens = len(
                tokenizer.encode(
                    remaining,
                    add_special_tokens=True,
                    truncation=True,
                    max_length=max_tokens + 1,
                )
            )

            if current_chunk_tokens + remaining_tokens <= max_tokens:
                current_chunk.append(remaining)
                current_chunk_tokens += remaining_tokens
            else:
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    chunks.append(
                        (current_chunk_start, chunk_text, current_chunk_tokens)
                    )
                    current_chunk_start += len(chunk_text)

                if remaining_tokens > max_tokens and weight > NO_WEIGHT:
                    sub_chunks = split_by_weight(
                        remaining, weight - 1, current_chunk_start
                    )
                    chunks.extend(sub_chunks)
                elif remaining_tokens <= max_tokens:
                    chunks.append((current_chunk_start, remaining, remaining_tokens))
                else:
                    raise ValueError(
                        "Cannot split remaining text within token limit; "
                        "consider increasing max_tokens"
                    )

        # Add final chunk if exists
        if current_chunk:
            chunk_text = "".join(current_chunk)
            chunks.append((current_chunk_start, chunk_text, current_chunk_tokens))

        return chunks

    def merge_chunks(chunks: List[Tuple[int, str, int]]) -> List[Tuple[int, str]]:
        """Greedily merge chunks to ensure consecutive chunks sum to at least max_tokens."""
        if not chunks:
            return []

        merged = []
        i = 0
        while i < len(chunks):
            current_start, current_text, current_tokens = chunks[i]
            current_chunk = current_text
            current_token_count = current_tokens
            current_start_idx = current_start

            # Look ahead to merge with next chunk if possible
            j = i + 1
            while j < len(chunks):
                next_start, next_text, next_tokens = chunks[j]
                combined_tokens = current_token_count + next_tokens

                # Check if merging is feasible
                if combined_tokens <= max_tokens:
                    # Check separator weight between chunks
                    separator = current_chunk[-1] if current_chunk else ""
                    separator_weight = get_weight(separator) if separator else NO_WEIGHT

                    # Only merge across low-weight separators (e.g., spaces, punctuation)
                    if separator_weight <= SPACE_WEIGHT:
                        current_chunk += next_text
                        current_token_count = combined_tokens
                        j += 1
                    else:
                        break  # Respect high-weight separator
                else:
                    break  # Exceeds max_tokens

            merged.append((current_start_idx, current_chunk))
            i = j

        return merged

    # Split text and track token counts
    initial_chunks = split_by_weight(text, PARAGRAPH_SEPARATOR_WEIGHT, 0)

    # Merge chunks greedily
    return merge_chunks(initial_chunks)
