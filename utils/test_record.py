class TestRecord:

    def __init__(self):
        self.index:            int = 0
        self.test_time:        str = ""
        self.balance_before:   int = 0
        self.bet:              int = 0
        self.win_displayed:    int = 0
        self.balance_after:    int = 0
        self.expected_balance: int = 0
        self.pass_fail:        str = ""
        self.fail_reason:      str = ""

    def validate(self) -> bool:
        self.expected_balance = self.balance_before - self.bet + self.win_displayed
        reasons = []

        if self.balance_after != self.expected_balance:
            reasons.append(f"金流異常(差{self.balance_after - self.expected_balance:+d})")
        if self.balance_after < 0:
            reasons.append("餘額出現負值")
        if self.win_displayed < 0:
            reasons.append("贏分出現負值")
        if self.bet > self.balance_before:
            reasons.append("押注超過餘額仍可下注")

        self.pass_fail   = "FAIL" if reasons else "PASS"
        self.fail_reason = " | ".join(reasons) if reasons else "-"
        return not bool(reasons)
