"""Option pricing Q and artificial operating-scenario R are distinct laws."""
SCENARIO_LAW = "conditional_option_implied_shape"


def measure_contract(valuation_law: str = SCENARIO_LAW) -> dict:
    if valuation_law != SCENARIO_LAW:
        raise ValueError("Only a conditional scenario law is implemented; Q-to-P and corporate Q pricing are not validated")
    return {
        "option_calibration_measure": "Q: deterministic-rate European pricing approximation after American adjustment",
        "operating_simulation_law": "R: artificial conditional scenario law; neither validated P nor the option-pricing Q",
        "q_to_p_change_of_measure": "NOT_IMPLEMENTED",
        "radon_nikodym_density": "NOT_ESTIMATED",
        "physical_risk_premia": "NOT_ESTIMATED: price, variance, jump intensity/marks and convenience yield",
        "gold_scenario": "GLD option-implied coefficients transferred to a separately dated realized-gold anchor and assumed drift; not a traded gold Q process",
        "copper_scenario": "Cross-delivery anchors imposed as a deterministic mean schedule; not the time drift of a fixed-delivery HG future",
        "fixed_delivery_future_pricing_drift": "ZERO under the deterministic-rate pricing convention; rates discount option premia",
        "jump_compensation": "lambda * (E[exp(J)] - 1), or left-step Hawkes intensity times that moment, under the simulated mark law",
        "discount_law": "Independent assumed WACC shocks; WACC is not the short rate or an estimated stochastic discount factor",
        "q_cash_flows_plus_wacc": "No corporate-pricing interpretation; may mix incompatible risk adjustments",
        "numeraire_change": "NONE; option normalization does not estimate physical probabilities",
        "joint_commodity_measure": "No common pricing kernel or joint P/Q law estimated; independence and terminal-score copulas are scenario assumptions",
        "permitted_output": "Conditional discounted operating proxy only; no physical probability, fair value or per-share target",
    }
