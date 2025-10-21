"""
Confidence Tracking System for Adaptive Learning

This module implements confidence tracking and calibration calculations
for the adaptive learning system.
"""

from typing import Dict, Literal
from datetime import datetime


CalibrationLevel = Literal[
    "calibrated",
    "slightly_overconfident",
    "slightly_underconfident",
    "moderately_overconfident",
    "moderately_underconfident",
    "significantly_miscalibrated"
]


def map_score_to_confidence(score: float) -> int:
    """
    Map an assessment score (0.0-1.0) to expected confidence level (1-5).

    This represents what confidence level SHOULD match the performance.

    Args:
        score: Assessment score from 0.0 to 1.0

    Returns:
        Expected confidence level (1-5)
    """
    if score <= 0.20:
        return 1  # Very poor performance → should not be confident
    elif score <= 0.50:
        return 2  # Poor performance → low confidence appropriate
    elif score <= 0.75:
        return 3  # Moderate performance → moderate confidence
    elif score <= 0.90:
        return 4  # Good performance → high confidence
    else:
        return 5  # Excellent performance → very high confidence


def calculate_calibration(self_confidence: int, actual_score: float) -> Dict:
    """
    Calculate calibration between self-reported confidence and actual performance.

    Args:
        self_confidence: Student's confidence rating (1-5)
        actual_score: Actual assessment score (0.0-1.0)

    Returns:
        Dictionary containing calibration analysis
    """
    # Map score to what confidence should be
    expected_confidence = map_score_to_confidence(actual_score)

    # Calculate error (positive = overconfident, negative = underconfident)
    error = self_confidence - expected_confidence

    # Categorize calibration
    if error == 0:
        calibration = "calibrated"
        direction = "calibrated"
    elif error == 1:
        calibration = "slightly_overconfident"
        direction = "overconfident"
    elif error == -1:
        calibration = "slightly_underconfident"
        direction = "underconfident"
    elif error == 2:
        calibration = "moderately_overconfident"
        direction = "overconfident"
    elif error == -2:
        calibration = "moderately_underconfident"
        direction = "underconfident"
    elif error >= 3:
        calibration = "significantly_miscalibrated"
        direction = "overconfident"
    else:  # error <= -3
        calibration = "significantly_miscalibrated"
        direction = "underconfident"

    return {
        "self_confidence": self_confidence,
        "actual_score": actual_score,
        "expected_confidence": expected_confidence,
        "calibration_error": error,
        "calibration": calibration,
        "direction": direction,
        "timestamp": datetime.now().isoformat()
    }


def get_calibration_feedback(calibration_data: Dict) -> str:
    """
    Generate appropriate feedback message based on calibration analysis.

    Args:
        calibration_data: Output from calculate_calibration()

    Returns:
        Feedback string for the student
    """
    self_conf = calibration_data["self_confidence"]
    actual = calibration_data["actual_score"]
    expected = calibration_data["expected_confidence"]
    error = calibration_data["calibration_error"]

    # Calibrated responses
    if error == 0:
        return f"Your confidence ({self_conf}/5) matches your understanding perfectly - excellent self-awareness!"

    # Overconfident responses
    elif error == 1:
        return f"You were slightly overconfident (rated {self_conf}/5, performance was {expected}/5 level), but you're close to calibrated. Keep refining your self-assessment."
    elif error == 2:
        return f"You rated your confidence as {self_conf}/5, but your performance was at a {expected}/5 level. Let's identify the gap in understanding so you can calibrate better."
    elif error >= 3:
        return f"I notice you were very confident ({self_conf}/5) but scored {actual:.0%}. This suggests a gap we need to address. Let's review the concept to build accurate understanding."

    # Underconfident responses
    elif error == -1:
        return f"You were slightly underconfident (rated {self_conf}/5, but performed at {expected}/5 level). You're doing better than you think!"
    elif error == -2:
        return f"You rated {self_conf}/5 confidence, but your performance was {expected}/5 level - quite strong! Trust your understanding more."
    else:  # error <= -3
        return f"You rated your confidence as {self_conf}/5, but you scored {actual:.0%} - that's excellent! You have stronger understanding than you realize. What made you feel uncertain?"


def calculate_overall_calibration(confidence_history: list) -> Dict:
    """
    Calculate overall calibration metrics from a learner's history.

    Args:
        confidence_history: List of calibration data dictionaries

    Returns:
        Overall calibration metrics
    """
    if not confidence_history:
        return {
            "overall_accuracy": 0.0,
            "overconfidence_rate": 0.0,
            "underconfidence_rate": 0.0,
            "calibrated_rate": 0.0
        }

    total = len(confidence_history)
    overconfident_count = 0
    underconfident_count = 0
    calibrated_count = 0
    total_error = 0

    for item in confidence_history:
        error = item.get("error", 0)
        total_error += abs(error)

        if error > 0:
            overconfident_count += 1
        elif error < 0:
            underconfident_count += 1
        else:
            calibrated_count += 1

    # Calculate average absolute error (lower is better, 0 = perfect)
    avg_error = total_error / total

    # Convert to accuracy (inverse of error, scaled 0-1)
    # Error of 0 = accuracy of 1.0
    # Error of 4 = accuracy of 0.2
    # Error of 5 = accuracy of 0.0
    accuracy = max(0.0, 1.0 - (avg_error / 5.0))

    return {
        "overall_accuracy": round(accuracy, 2),
        "average_error": round(avg_error, 2),
        "overconfidence_rate": round(overconfident_count / total, 2),
        "underconfidence_rate": round(underconfident_count / total, 2),
        "calibrated_rate": round(calibrated_count / total, 2),
        "total_assessments": total
    }


def detect_calibration_trend(confidence_history: list, window_size: int = 5) -> str:
    """
    Detect whether calibration is improving, stable, or degrading.

    Args:
        confidence_history: List of calibration data (chronological order)
        window_size: Number of recent assessments to compare against older ones

    Returns:
        Trend description: "improving", "stable", "degrading", or "insufficient_data"
    """
    if len(confidence_history) < window_size * 2:
        return "insufficient_data"

    # Calculate error for recent window
    recent = confidence_history[-window_size:]
    recent_errors = [abs(item.get("error", 0)) for item in recent]
    recent_avg = sum(recent_errors) / len(recent_errors)

    # Calculate error for older window (same size, immediately before recent)
    older = confidence_history[-(window_size * 2):-window_size]
    older_errors = [abs(item.get("error", 0)) for item in older]
    older_avg = sum(older_errors) / len(older_errors)

    # Compare averages
    improvement = older_avg - recent_avg

    if improvement > 0.5:
        return "improving"
    elif improvement < -0.5:
        return "degrading"
    else:
        return "stable"


def should_intervene_on_confidence(
    calibration_data: Dict,
    performance_score: float,
    history_length: int
) -> tuple[bool, str]:
    """
    Determine if AI agent should intervene based on confidence-performance gap.

    Args:
        calibration_data: Current calibration analysis
        performance_score: Current assessment score
        history_length: Number of prior assessments for this concept

    Returns:
        Tuple of (should_intervene: bool, reason: str)
    """
    error = calibration_data["calibration_error"]

    # Severe overconfidence + poor performance = immediate intervention
    if error >= 3 and performance_score < 0.50:
        return (
            True,
            "Severe overconfidence with poor performance - major misconception likely"
        )

    # Severe underconfidence + good performance = encourage
    if error <= -3 and performance_score >= 0.75:
        return (
            True,
            "Severe underconfidence despite strong performance - needs encouragement"
        )

    # Persistent overconfidence (even moderate) = intervention
    if error >= 2 and history_length >= 3:
        return (
            True,
            "Persistent overconfidence pattern - help learner develop accurate self-assessment"
        )

    # Otherwise, standard feedback is sufficient
    return (False, "Normal calibration feedback appropriate")


# Example usage
if __name__ == "__main__":
    # Example 1: Well-calibrated student
    print("Example 1: Well-calibrated student")
    calibration = calculate_calibration(self_confidence=4, actual_score=0.85)
    print(f"Calibration: {calibration['calibration']}")
    print(f"Feedback: {get_calibration_feedback(calibration)}")
    print()

    # Example 2: Overconfident student
    print("Example 2: Overconfident student")
    calibration = calculate_calibration(self_confidence=5, actual_score=0.60)
    print(f"Calibration: {calibration['calibration']}")
    print(f"Feedback: {get_calibration_feedback(calibration)}")
    print()

    # Example 3: Underconfident student
    print("Example 3: Underconfident student")
    calibration = calculate_calibration(self_confidence=2, actual_score=0.95)
    print(f"Calibration: {calibration['calibration']}")
    print(f"Feedback: {get_calibration_feedback(calibration)}")
    print()

    # Example 4: Calibration history analysis
    print("Example 4: Calibration metrics over time")
    history = [
        {"error": 2},   # Overconfident
        {"error": 1},   # Slightly overconfident
        {"error": -1},  # Slightly underconfident
        {"error": 0},   # Calibrated
        {"error": 0},   # Calibrated
        {"error": 1},   # Slightly overconfident
        {"error": 0},   # Calibrated
    ]
    metrics = calculate_overall_calibration(history)
    print(f"Overall accuracy: {metrics['overall_accuracy']}")
    print(f"Calibrated rate: {metrics['calibrated_rate']}")
    print(f"Overconfidence rate: {metrics['overconfidence_rate']}")
    print(f"Underconfidence rate: {metrics['underconfidence_rate']}")
    print()

    # Example 5: Trend detection
    print("Example 5: Calibration trend")
    improving_history = [
        {"error": 3}, {"error": 2}, {"error": 2}, {"error": 1}, {"error": 1},
        {"error": 1}, {"error": 0}, {"error": 0}, {"error": -1}, {"error": 0}
    ]
    trend = detect_calibration_trend(improving_history)
    print(f"Trend: {trend}")
    print()

    # Example 6: Intervention decision
    print("Example 6: Should intervene?")
    severe_overconf = calculate_calibration(self_confidence=5, actual_score=0.40)
    should_intervene, reason = should_intervene_on_confidence(
        severe_overconf,
        performance_score=0.40,
        history_length=4
    )
    print(f"Intervene: {should_intervene}")
    print(f"Reason: {reason}")
