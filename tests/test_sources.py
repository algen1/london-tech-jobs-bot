"""Parsers are tested against trimmed-down copies of real API responses."""

from jobbot.notifier import job_to_embed
from jobbot.sources import adzuna, company_boards, google_jobs, reed


def test_adzuna():
    data = {
        "results": [
            {
                "title": "Graduate Software Engineer ",
                "company": {"display_name": "Acme Ltd"},
                "location": {"display_name": "City of London, London"},
                "redirect_url": "https://adzuna.co.uk/1",
                "created": "2026-10-20T09:00:00Z",
                "salary_min": 32000,
                "salary_max": 36000,
            }
        ]
    }
    [job] = adzuna.parse_results(data)
    assert job.title == "Graduate Software Engineer"
    assert job.company == "Acme Ltd"
    assert job.salary == "£32,000 - £36,000"
    assert job.posted.year == 2026


def test_reed():
    data = {
        "results": [
            {
                "jobTitle": "Junior Developer",
                "employerName": "Beta",
                "locationName": "London",
                "jobUrl": "https://reed.co.uk/2",
                "date": "21/10/2026",
                "minimumSalary": 30000.0,
                "maximumSalary": None,
            }
        ]
    }
    [job] = reed.parse_results(data)
    assert job.posted.day == 21 and job.posted.month == 10
    assert job.salary == "£30,000"


def test_google_jobs_prefers_apply_link():
    data = {
        "jobs_results": [
            {
                "title": "Tech Intern",
                "company_name": "Gamma",
                "location": "London, UK",
                "apply_options": [{"title": "Gamma Careers", "link": "https://gamma.com/apply"}],
                "share_link": "https://google.com/share",
            }
        ]
    }
    assert google_jobs.parse_results(data)[0].url == "https://gamma.com/apply"


def test_greenhouse():
    data = {
        "jobs": [
            {
                "title": "Graduate Engineer",
                "company_name": "Monzo",
                "location": {"name": "Cardiff, London or Remote (UK)"},
                "absolute_url": "https://job-boards.greenhouse.io/monzo/jobs/1",
                "first_published": "2026-08-24T09:04:42-04:00",
            }
        ]
    }
    [job] = company_boards.parse_greenhouse(data, "monzo")
    assert job.company == "Monzo" and "London" in job.location


def test_lever():
    data = [
        {
            "text": "2027 Graduate Analyst",
            "categories": {"location": "London", "allLocations": ["London"]},
            "hostedUrl": "https://jobs.lever.co/zopa/1",
            "createdAt": 1787913476287,
        }
    ]
    [job] = company_boards.parse_lever(data, "zopa")
    assert job.company == "Zopa" and job.location == "London"
    assert job.posted is not None


def test_ashby_skips_unlisted_and_merges_locations():
    data = {
        "jobs": [
            {
                "title": "ML Intern",
                "location": "Paris",
                "secondaryLocations": [{"location": "London"}],
                "jobUrl": "https://jobs.ashbyhq.com/x/1",
                "isListed": True,
            },
            {"title": "Hidden", "location": "London", "jobUrl": "u", "isListed": False},
        ]
    }
    jobs = company_boards.parse_ashby(data, "wayve")
    assert [j.title for j in jobs] == ["ML Intern"]
    assert jobs[0].location == "Paris, London"


def test_discord_embed_shape():
    [job] = company_boards.parse_lever(
        [{"text": "Intern", "categories": {"location": "London"}, "hostedUrl": "https://u", "createdAt": 0}], "zopa"
    )
    embed = job_to_embed(job)
    assert embed["title"] == "Intern" and embed["url"] == "https://u"
    assert {"name": "Company", "value": "Zopa", "inline": True} in embed["fields"]
