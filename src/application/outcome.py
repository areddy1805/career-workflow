from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ApplicationStatus(str, Enum):
    APPLIED_SUCCESSFULLY = "applied_successfully"
    APPLICATION_SUBMITTED = "application_submitted"
    ALREADY_APPLIED = "already_applied"
    EXTERNAL_AUTOMATION_COMPLETED = "external_automation_completed"
    QUEUED_FOR_PLAYWRIGHT = "queued_for_playwright"
    QUEUED_FOR_MANUAL_REVIEW = "queued_for_manual_review"
    PROVIDER_UNSUPPORTED = "provider_unsupported"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION_FAILED = "authentication_failed"
    PROVIDER_ERROR = "provider_error"
    APPLICATION_FAILED = "application_failed"
    SKIPPED_BY_POLICY = "skipped_by_policy"
    QUESTIONNAIRE_REQUIRED = "questionnaire_required"
    PROFILE_DATA_REQUIRED = "profile_data_required"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ApplicationOutcome:
    status: ApplicationStatus
    job_id: str
    response: dict[str, Any]
    questionnaire: list[dict[str, Any]] = field(default_factory=list)
    validation_errors: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str | None = None

    @property
    def applied(self) -> bool:
        return self.status in {
            ApplicationStatus.APPLIED_SUCCESSFULLY,
            ApplicationStatus.APPLICATION_SUBMITTED,
        }

    @property
    def requires_questionnaire(self) -> bool:
        return self.status == ApplicationStatus.QUESTIONNAIRE_REQUIRED

    @property
    def requires_profile_data(self) -> bool:
        return self.status == ApplicationStatus.PROFILE_DATA_REQUIRED

    @property
    def failed(self) -> bool:
        return self.status in {
            ApplicationStatus.APPLICATION_FAILED,
            ApplicationStatus.PROVIDER_ERROR,
            ApplicationStatus.AUTHENTICATION_FAILED,
            ApplicationStatus.UNKNOWN,
        }
