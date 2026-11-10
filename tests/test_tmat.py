import numpy as np
import pandas as pd
from model.tmat_model import model_tmat_v5, simulate_daily
from model.evaluation import hitung_metrik


def test_below_surface():
    result = model_tmat_v5([0, 0], [4, 4], wtd_awal=-.5, Sy=.5, WF_below=1)
    assert np.allclose(result.WTD, [-.51, -.52])
    assert np.allclose(result.ET_WF, [5, 5])


def test_above_surface_clamp():
    result = model_tmat_v5([1000], [4], wtd_awal=-.1, Sy=.5, WF_above=45)
    assert result.WTD.iloc[0] == 0
    assert result.ET_WF.iloc[0] == 49


def test_metrics_perfect():
    met = hitung_metrik([-1, -2, -3], [-1, -2, -3])
    assert np.isclose(met['KGE'], 1)
    assert np.isclose(met['PBIAS'], 0)


def test_daily_continuity():
    df = pd.DataFrame({'date': ['2001-01-01', '2001-01-03'], 'rain_mm': [0, 0], 'ET0': [4, 4]})
    try:
        simulate_daily(df, {'Sy': .48, 'WF_below': 1, 'WF_above': 45})
        assert False, 'Expected ValueError'
    except ValueError:
        pass
