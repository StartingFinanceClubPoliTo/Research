import numpy as np
import pandas as pd
from barrick_unified.copper import copper_surface,american_futures_price
from barrick_unified.ib_gold_surface import black76_price,build_observed_surface

def test_explicit_historical_curve_is_used_instead_of_september_manual_curve():
    rate=.017
    price=black76_price(6.,6.3,.5,rate,.3,'C')
    f=pd.DataFrame([dict(option_con_id=1,option_expiry='20270126',right='C',strike=6.3,future_mid=6.,
        maturity_years_act36525=.5,quote_age_seconds=1.,bid=price*.99,ask=price*1.01,mid=price)])
    out,meta=build_observed_surface(f,rate_curve=lambda ts:np.full(np.asarray(ts).shape,rate),
                                  rate_metadata={'curve_date':'2026-07-09'})
    assert out.rate.iloc[0]==rate
    assert abs(out.implied_vol.iloc[0]-.3)<1e-8
    assert meta['nss_fit']['curve_date']=='2026-07-09'

def test_american_adjustment_uses_the_date_specific_rate():
    rate=.019
    price=american_futures_price(6.,6.3,.5,rate,.3,'C',600)
    f=pd.DataFrame([dict(option_con_id=1,option_expiry='20270126',right='C',strike=6.3,future_mid=6.,
        maturity_years_act36525=.5,quote_age_seconds=1.,future_quote_age_seconds=1.,
        bid=price*.99,ask=price*1.01,mid=price,quote_unit='USD/lb',trading_class='HXE',underlying_verified=True)])
    out,meta=copper_surface(f,rate_curve=lambda ts:np.full(np.asarray(ts).shape,rate),
                           rate_metadata={'curve_date':'2026-07-09'})
    assert abs(out.implied_vol.iloc[0]-.3)<1e-7
    assert out.rate.iloc[0]==rate
