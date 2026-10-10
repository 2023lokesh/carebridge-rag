"""Regression tests for disease-specific, cited vaccine answers."""
import pytest
from carebridge.rag import answer

@pytest.mark.parametrize("question", [
    "What is the Covid vaccine for?",
    "What is the COVID-19 vaccine for?",
    "What does the coronavirus vaccine protect against?",
])
def test_covid_never_substitutes_other_vaccines(question):
    result = answer(question)
    assert result["refused"] is False
    body = result["answer"].lower()
    assert "covid" in body
    assert "severe illness" in body or "prevent covid" in body
    assert "hpv" not in body and "mmrv" not in body
    assert "myocarditis" not in body  # A benefits query must not drift into adverse reactions.
    assert result["sources"]
    assert all("/covid/" in x["url"] or "covid-19" in x["url"] for x in result["sources"])

def test_side_effects_are_specific_to_the_vaccine():
    result = answer("What are the side effects of a COVID vaccine?")
    assert result["refused"] is False
    assert "headache" in result["answer"].lower()
    assert all("/covid/" in s["url"] or "covid-19" in s["url"] for s in result["sources"])

@pytest.mark.parametrize("question", [
    "What is the flu vaccine for?",
    "What is a pneumococcal vaccine for?",
    "How are COVID and flu vaccines different?",
])
def test_unavailable_or_partly_unavailable_topics_refuse(question):
    result = answer(question)
    assert result["refused"] is True
    assert result["sources"] == []
