from .adzuna import AdzunaSource
from .company_boards import AshbySource, GreenhouseSource, LeverSource
from .google_jobs import GoogleJobsSource
from .reed import ReedSource

# config.yaml key -> source class
SOURCES = {
    "adzuna": AdzunaSource,
    "reed": ReedSource,
    "google_jobs": GoogleJobsSource,
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "ashby": AshbySource,
}
