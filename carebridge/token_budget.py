"""Exact tokenizer-aware splitting to prevent evidence loss from embedding truncation.

Uses Hugging Face *fast* tokenizer character offsets, retaining original source text
rather than decoding wordpieces. Never includes student evaluation/test data.
"""
from .corpus import stable_id


def enforce_model_token_budget(chunks, tokenizer, max_seq_length, overlap_tokens=24, safety_margin=2):
    """Return chunks within an embedding model's actual WordPiece limit.

    Each oversized chunk is split by source character offsets from tokenizer
    wordpieces. Short chunks stay byte-identical, long chunks preserve text
    in overlapping source slices; IDs are deterministic across rebuilds.
    """
    specials = int(tokenizer.num_special_tokens_to_add(pair=False))
    budget = int(max_seq_length) - specials - safety_margin
    if budget <= overlap_tokens or overlap_tokens < 0:
        raise ValueError('Insufficient token budget or invalid overlap')
    out, seen = [], set()
    oversized = 0
    for chunk in chunks:
        text = chunk['text']
        encoded = tokenizer(text, add_special_tokens=False, truncation=False,
                            return_offsets_mapping=True)
        offsets = encoded['offset_mapping']
        # Only fast tokenizers can accurately map wordpiece spans to original text.
        if len(offsets) and not isinstance(offsets[0], (tuple, list)):
            raise ValueError('Tokenizer did not return source offsets')
        if len(offsets) <= budget:
            pieces = [(0, len(text))]
        else:
            oversized += 1
            pieces = []
            start = 0
            while start < len(offsets):
                end = min(len(offsets), start + budget)
                left, right = offsets[start][0], offsets[end - 1][1]
                if right <= left:
                    raise ValueError('Tokenizer offset mapping cannot slice source text')
                pieces.append((left, right))
                if end == len(offsets):
                    break
                start = end - overlap_tokens
        for subindex, (left, right) in enumerate(pieces):
            child = dict(chunk)
            if len(pieces) > 1:
                child['text'] = text[left:right]
                child['parent_chunk_id'] = chunk['chunk_id']
                child['token_window_index'] = subindex
                child['chunk_id'] = stable_id(chunk['chunk_id'], 'model-budget-v1', str(left), str(right))
            if child['chunk_id'] in seen:
                continue
            seen.add(child['chunk_id'])
            out.append(child)
    return out, {'chunks_pre_budget':len(chunks), 'chunks_over_budget_before':oversized,
                 'chunks_post_budget':len(out), 'token_payload_budget':budget,
                 'overlap_model_tokens':overlap_tokens}
