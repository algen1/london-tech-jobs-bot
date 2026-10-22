from pathlib import Path

import pytest

from jobbot.filters import JobFilter, dedupe
from jobbot.main import load_config
from jobbot.models import Job

CONFIG = load_config(Path(__file__).parent.parent / "config.yaml")


@pytest.fixture
def job_filter():
    return JobFilter.from_config(CONFIG)


def make_job(title, company="Acme", location="London, UK"):
    return Job(title=title, company=company, location=location, url="https://x", source="Test")


@pytest.mark.parametrize(
    "title",
    [
        "Graduate Software Engineer",
        "2027 Software Engineering Internship - London",
        "Junior Data Analyst",
        "Summer Intern, Machine Learning",
        "Technology Graduate Scheme",
        "Cyber Security Graduate",
        "Entry-Level Cloud Engineer",
        "New Grad Backend Developer",
        "Graduate IT Consultant",
    ],
)
def test_keeps_early_career_tech_roles(job_filter, title):
    assert job_filter(make_job(title))


@pytest.mark.parametrize(
    "title",
    [
        "Senior Software Engineer",
        "Graduate Sales Executive",  # not tech
        "Software Engineer",  # not early career
        "Lead Data Scientist",
        "Software Engineering Placement Year",  # placements excluded
        "Graduate Mechanical Engineer",
        "Staff Engineer, Platform",
        "Marketing Intern",
    ],
)
def test_rejects_other_roles(job_filter, title):
    assert not job_filter(make_job(title))


def test_word_boundaries(job_filter):
    # "it" inside "Recruitment" and "ai" inside "Maintenance" must not count as tech
    assert not job_filter(make_job("Graduate Recruitment Coordinator"))
    assert not job_filter(make_job("Junior Maintenance Assistant"))


def test_location(job_filter):
    title = "Graduate Software Engineer"
    assert job_filter(make_job(title, location="London, United Kingdom"))
    assert job_filter(make_job(title, location="Remote (UK)"))
    assert not job_filter(make_job(title, location="New York, NY"))
    assert job_filter(make_job(title, location="New York, NY"), check_location=False)


def test_dedupe_across_sources():
    a = make_job("Graduate Software Engineer", company="Monzo")
    b = make_job("Graduate Software Engineer!", company="monzo")
    c = make_job("Software Engineering Intern", company="Monzo")
    assert dedupe([a, b, c]) == [a, c]
