from core.functions.default_token_estimator import default_token_estimator

def test_default_token_estimator():
    assert default_token_estimator("") == 0
    assert default_token_estimator("hello world") > 0
