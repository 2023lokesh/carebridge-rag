"""Independent tokenizer budget and provenance regression tests."""
import re
from carebridge.token_budget import enforce_model_token_budget


class WordTokenizer:
    """Deterministic wordpiece surrogate used only to test exact offset handling."""
    def num_special_tokens_to_add(self, pair=False):
        return 2

    def __call__(self, text, add_special_tokens=False, truncation=False,
                 return_offsets_mapping=False):
        offsets=[m.span() for m in re.finditer(r'\S+',text)]
        return {'offset_mapping':offsets}


def test_budget_splits_oversized_into_exact_source_substrings():
    text=' '.join(f'word{x}' for x in range(100))
    docs=[{'chunk_id':'parent01','text':text,'url':'https://www.cdc.gov/example','title':'X'}]
    result,stats=enforce_model_token_budget(docs,WordTokenizer(),max_seq_length=20,
                                            overlap_tokens=4,safety_margin=2)
    assert stats['chunks_pre_budget']==1
    assert stats['chunks_over_budget_before']==1
    assert len(result)>1
    assert len({d['chunk_id'] for d in result})==len(result)
    for d in result:
        assert d['text'] in text
        assert len(d['text'].split())<=16
        assert d['parent_chunk_id']=='parent01'
    combined=' '.join(d['text'] for d in result)
    assert all(word in combined.split() for word in text.split())
    assert result[0]['text'].split()[-4:]==result[1]['text'].split()[:4]


def test_unchanged_for_safe_chunks_and_repeatable_ids():
    input_=[{'chunk_id':'abc','text':'two words','url':'https://www.cdc.gov/example'}]
    one,info=enforce_model_token_budget(input_,WordTokenizer(),256)
    two,_=enforce_model_token_budget(input_,WordTokenizer(),256)
    assert one==two==input_
    assert info['chunks_over_budget_before']==0


def test_invalid_model_limit_rejected():
    try:
        enforce_model_token_budget([],WordTokenizer(),20,overlap_tokens=18)
    except ValueError:pass
    else:raise AssertionError('Expected invalid budget rejection')
