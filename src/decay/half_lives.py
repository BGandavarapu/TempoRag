from src.ingestion.document import Domain

HALF_LIVES: dict[Domain, int] = {
    Domain.MEDICAL: 730,
    Domain.LEGAL: 1825,
    Domain.FINANCIAL: 365,
    Domain.SCIENTIFIC: 1095,
    Domain.NEWS: 30,
    Domain.GENERAL: 365,
}


def get_half_life(domain: Domain) -> int:
    return HALF_LIVES[domain]
