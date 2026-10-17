from fractions import Fraction

from uniform_lab.proofs import FarkasCertificate, SmtProofTrace


def test_farkas_certificate_valid() -> None:
    # System: x <= 1, -x <= -2  (i.e. x <= 1 and x >= 2, which is infeasible)
    # Matrix A: [[1], [-1]], bounds b: [1, -2]
    # Multipliers lambda: [1, 1]
    # lambda^T A = 1*1 + 1*(-1) = 0
    # lambda^T b = 1*1 + 1*(-2) = -1 < 0
    cert = FarkasCertificate(
        matrix=((Fraction(1),), (Fraction(-1),)),
        bounds=(Fraction(1), Fraction(-2)),
        multipliers=(Fraction(1), Fraction(1)),
    )
    valid, msg = cert.verify()
    assert valid is True
    assert "infeasibility verified" in msg
    assert cert.to_dict()["valid"] is True


def test_farkas_certificate_invalid_sign() -> None:
    # Negative multiplier should fail
    cert = FarkasCertificate(
        matrix=((Fraction(1),), (Fraction(-1),)),
        bounds=(Fraction(1), Fraction(-2)),
        multipliers=(Fraction(-1), Fraction(1)),
    )
    valid, msg = cert.verify()
    assert valid is False
    assert "negative" in msg


def test_smt_proof_trace_parse_and_verify() -> None:
    proof_text = """(step t1 (cl (not p) q) :rule resolution :premises ())
(step t2 (cl p) :rule assume :premises ())
(step t3 (cl q) :rule resolution :premises (t1 t2))
(step t4 (cl (not q)) :rule assume :premises ())
(step t5 (cl false) :rule resolution :premises (t3 t4))"""

    trace = SmtProofTrace.parse(proof_text)
    assert len(trace.steps) == 5
    assert trace.concludes_false is True
    valid, msg = trace.verify()
    assert valid is True
    assert "proof verified" in msg
    assert trace.to_dict()["valid"] is True
