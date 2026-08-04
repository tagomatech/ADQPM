import pandas as pd
import pytest

from agpm.corn_quotes import normalize_corn_history


def test_corn_quote_unit_conversion_is_explicit():
    frame = pd.DataFrame({"value": [451.75, 500.0]})
    result = normalize_corn_history(frame)
    assert result["raw_value"].tolist() == [451.75, 500.0]
    assert result["value"].tolist() == pytest.approx([4.5175, 5.0])
    assert set(result["unit"]) == {"USD/bushel"}
