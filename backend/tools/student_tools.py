"""Student-specific tools are unavailable until an authorization policy exists."""


class StudentToolAuthorizationError(PermissionError):
	"""Raised when a student-data operation lacks approved authorization."""


def get_student_tools() -> dict[str, object]:
	"""Return no student-record tools for unauthenticated assistant requests."""
	return {}