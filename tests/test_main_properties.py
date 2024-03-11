from hypothesis import given, strategies as st
from main import get_se_cost

# Property-based test for get_se_cost function
@given(st.dictionaries(keys=st.just("cost"), values=st.one_of(st.integers(min_value=0), st.just("X"), st.none())))
def test_get_se_cost_properties(card):
    cost = get_se_cost(card)
    assert cost.isdigit() or cost in ["X", "-"]
    if "cost" in card:
        if card["cost"] is None:
            assert cost == "-"
        elif isinstance(card["cost"], int):
            assert cost == str(card["cost"])
        elif card["cost"] == "X":
            assert cost == "X"
