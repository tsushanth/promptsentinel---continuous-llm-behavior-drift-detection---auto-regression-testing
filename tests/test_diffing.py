from promptsentinel.diffing import compare


def test_json_still_parses_no_flag():
    result = compare("p", '{"a": 1}', '{"a": 1}')
    assert result.status == "OK"


def test_json_becomes_malformed_flags_regression():
    result = compare("p", '{"a": 1}', '{"a": 1')
    assert result.status == "REGRESSED"
    assert result.reason_code == "json_parse_regression"


def test_compliant_answer_becomes_refusal():
    result = compare(
        "p", "Sure, here is the answer: 42.",
        "I'm sorry, but I can't help with that.",
    )
    assert result.status == "REGRESSED"
    assert result.reason_code == "refusal_regression"


def test_near_identical_text_no_flag():
    result = compare("p", "The capital of France is Paris.", "The capital of France is Paris!")
    assert result.status == "OK"


def test_divergent_text_flags_content_drift():
    baseline = "The capital of France is Paris, a city known for the Eiffel Tower."
    new = "Bananas are a good source of potassium and grow in tropical climates."
    result = compare("p", baseline, new)
    assert result.status == "REGRESSED"
    assert result.reason_code == "content_drift"


def test_verbose_blowup_flags_length_drift():
    baseline = "Photosynthesis turns sunlight into chemical energy."
    new = "Photosynthesis " * 40
    result = compare("p", baseline, new)
    assert result.status == "REGRESSED"
    assert result.reason_code == "length_drift"
