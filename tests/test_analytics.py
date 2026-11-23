"""
test_analytics.py — Unit tests for class dashboard analytics and evidence-based support insights
"""

import unittest
from backend.services.analytics_service import get_class_dashboard_analytics
from backend.services.assessment_service import get_student_assessment, update_student_assessment
from backend.services.insight_service import generate_class_support_insights, generate_student_observations


class TestAnalyticsAndInsights(unittest.TestCase):

    def test_class_dashboard_analytics_structure(self):
        """Class analytics computes enrollment, averages, component averages, and distributions."""
        analytics = get_class_dashboard_analytics(1)  # BSIT Section A
        self.assertEqual(analytics["class_id"], 1)
        self.assertGreaterEqual(analytics["total_enrolled"], 30)
        self.assertGreater(analytics["complete_records_count"], 0)
        self.assertGreater(analytics["incomplete_records_count"], 0)
        self.assertIsNotNone(analytics["average_total_marks"])
        self.assertLessEqual(analytics["average_total_marks"], 40.0)

        # Component averages
        comp_avgs = analytics["component_averages"]
        self.assertIn("midterm", comp_avgs)
        self.assertIn("assignment", comp_avgs)
        self.assertIn("presentation", comp_avgs)
        self.assertIn("attendance", comp_avgs)
        self.assertIn("sessional", comp_avgs)

        self.assertEqual(comp_avgs["midterm"]["max"], 30.0)
        self.assertEqual(comp_avgs["assignment"]["max"], 3.0)
        self.assertEqual(comp_avgs["presentation"]["max"], 3.0)
        self.assertEqual(comp_avgs["attendance"]["max"], 4.0)
        self.assertEqual(comp_avgs["sessional"]["max"], 10.0)

        # Score distribution bins
        dist = analytics["score_distribution"]
        self.assertIn("0–19.9", dist)
        self.assertIn("20–27.9", dist)
        self.assertIn("28–34.9", dist)
        self.assertIn("35–40.0", dist)
        total_in_bins = sum(dist.values())
        self.assertEqual(total_in_bins, analytics["complete_records_count"])

    def test_support_insights_generated(self):
        """Support insights identify incomplete records and divergence."""
        insights = generate_class_support_insights(1)
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)

        # Check structure of insight items
        first_insight = insights[0]
        self.assertIn("student_id", first_insight)
        self.assertIn("insight_type", first_insight)
        self.assertIn("description", first_insight)
        self.assertIn("recommendation", first_insight)
        self.assertIn("data_trace", first_insight)

        # Verify incomplete record insight exists
        incomplete_insights = [i for i in insights if i["insight_type"] == "Incomplete Assessment Record"]
        self.assertGreater(len(incomplete_insights), 0)

    def test_student_observations_feedback(self):
        """Individual observations generate evidence-based feedback without reductionist labels."""
        # Test complete strong record
        assessment = {
            "student_id": "TEST-001",
            "midterm_marks": 28.0,
            "assignment_marks": 2.8,
            "presentation_marks": 2.9,
            "attendance_marks": 3.8,
            "total_marks": 37.5,
            "is_complete": True,
            "missing_components": [],
        }
        obs = generate_student_observations(assessment)
        self.assertTrue(any("Consistent performance" in o for o in obs))

        # Test incomplete record
        incomplete_assessment = {
            "student_id": "TEST-002",
            "midterm_marks": 24.0,
            "assignment_marks": None,
            "presentation_marks": 2.5,
            "attendance_marks": 3.5,
            "total_marks": None,
            "is_complete": False,
            "missing_components": ["assignment"],
        }
        obs_inc = generate_student_observations(incomplete_assessment)
        self.assertTrue(any("incomplete" in o.lower() for o in obs_inc))

        # Test component divergence (strong exam, low assignment)
        divergent_assessment = {
            "student_id": "TEST-003",
            "midterm_marks": 27.0,  # 90%
            "assignment_marks": 0.9,  # 30%
            "presentation_marks": 2.8,
            "attendance_marks": 3.8,
            "total_marks": 34.5,
            "is_complete": True,
            "missing_components": [],
        }
        obs_div = generate_student_observations(divergent_assessment)
        self.assertTrue(any("divergence" in o.lower() for o in obs_div))


if __name__ == "__main__":
    unittest.main()
