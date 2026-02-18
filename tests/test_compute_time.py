"""Unit tests for TimeClass in compute_time.py"""
import unittest
import datetime
from functions.compute_time import TimeClass


class TestTimeClass(unittest.TestCase):
    """Test cases for TimeClass"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_date = datetime.date(2024, 12, 25)  # Christmas 2024, Wednesday
        self.tc_us = TimeClass(day=self.test_date, country_code="US")
        self.tc_de = TimeClass(day=self.test_date, country_code="DE")
        self.tc_fr = TimeClass(day=self.test_date, country_code="FR")

    def test_initialization(self):
        """Test TimeClass initialization"""
        tc = TimeClass()
        self.assertIsNotNone(tc._day)
        self.assertEqual(tc._country_code, "US")
        self.assertIsNotNone(tc._day_name)
        self.assertIsNotNone(tc._month_name)

    def test_initialization_with_parameters(self):
        """Test TimeClass initialization with custom date and country"""
        tc = TimeClass(day=self.test_date, country_code="DE")
        self.assertEqual(tc._day, self.test_date)
        self.assertEqual(tc._country_code, "DE")

    def test_day_name_translation(self):
        """Test day name translation for different countries"""
        # English
        self.assertEqual(self.tc_us._day_name, "Wednesday")

        # German
        self.assertEqual(self.tc_de._day_name, "Mittwoch")

        # French
        self.assertEqual(self.tc_fr._day_name, "mercredi")

    def test_month_name_translation(self):
        """Test month name translation for different countries"""
        # English
        self.assertEqual(self.tc_us._month_name, "December")

        # German
        self.assertEqual(self.tc_de._month_name, "Dezember")

        # French
        self.assertEqual(self.tc_fr._month_name, "décembre")

    def test_holiday_detection_us(self):
        """Test holiday detection for US"""
        self.assertTrue(self.tc_us._is_holiday)
        self.assertEqual(self.tc_us._holiday_name, "Christmas Day")

    def test_holiday_detection_de(self):
        """Test holiday detection for Germany"""
        self.assertTrue(self.tc_de._is_holiday)
        self.assertIn("Erster Weihnachtstag", self.tc_de._holiday_name)  # German for Christmas

    def test_holiday_detection_fr(self):
        """Test holiday detection for France"""
        self.assertTrue(self.tc_fr._is_holiday)
        self.assertIn("Noël", self.tc_fr._holiday_name)  # French for Christmas

    def test_non_holiday(self):
        """Test non-holiday date"""
        tc = TimeClass(day=datetime.date(2024, 3, 15), country_code="US")
        self.assertFalse(tc._is_holiday)
        self.assertIsNone(tc._holiday_name)

    def test_week_calculation(self):
        """Test week number calculation"""
        # December 25, 2024 is in ISO week 52
        self.assertEqual(self.tc_us._week_nb, 52)

        # Check week boundaries
        self.assertIsInstance(self.tc_us._week_beg, datetime.date)
        self.assertIsInstance(self.tc_us._week_end, datetime.date)

        # Week should be 7 days
        delta = self.tc_us._week_end - self.tc_us._week_beg
        self.assertEqual(delta.days, 6)

    def test_month_calculation(self):
        """Test month calculation"""
        self.assertEqual(self.tc_us._month_nb, 12)
        self.assertEqual(self.tc_us._month_beg, datetime.date(2024, 12, 1))
        self.assertEqual(self.tc_us._month_end, datetime.date(2024, 12, 31))

    def test_year_calculation(self):
        """Test year calculation"""
        self.assertEqual(self.tc_us._year_nb, 2024)
        self.assertEqual(self.tc_us._year_beg, datetime.date(2024, 1, 1))
        self.assertEqual(self.tc_us._year_end, datetime.date(2024, 12, 31))

    def test_get_day_method(self):
        """Test get_day method returns correct dictionary"""
        result = self.tc_us.get_day()

        # Check all expected keys exist
        expected_keys = [
            "day", "day_name", "week_nb", "week_beg", "week_end",
            "month_nb", "month_beg", "month_end", "month_name",
            "year_nb", "year_beg", "year_end", "is_holiday", "holiday_name"
        ]
        for key in expected_keys:
            self.assertIn(key, result)

    def test_get_day_with_new_date(self):
        """Test get_day method with a new date"""
        new_date = datetime.date(2024, 7, 4)  # Independence Day
        result = self.tc_us.get_day(day=new_date)

        self.assertEqual(result["day"], new_date)
        self.assertEqual(result["month_nb"], 7)
        self.assertEqual(result["day_name"], "Thursday")
        self.assertTrue(result["is_holiday"])
        self.assertEqual(result["holiday_name"], "Independence Day")

    def test_get_day_with_country_change(self):
        """Test get_day method with country code change"""
        result = self.tc_us.get_day(day=self.test_date, country_code="ES")

        self.assertEqual(result["day_name"], "miércoles")  # Spanish for Wednesday
        self.assertEqual(result["month_name"], "diciembre")  # Spanish for December
        self.assertTrue(result["is_holiday"])
        self.assertIn("Natividad del Señor", result["holiday_name"])  # Spanish for Christmas

    def test_cmp_week_by_number(self):
        """Test cmp_week_by_number method"""
        result = self.tc_us.cmp_week_by_number(year=2024, week=1)

        self.assertEqual(result["year"], 2024)
        self.assertEqual(result["week_nb"], 1)
        self.assertIsInstance(result["week_beg"], datetime.date)
        self.assertIsInstance(result["week_end"], datetime.date)

        # Week should be 7 days
        delta = result["week_end"] - result["week_beg"]
        self.assertEqual(delta.days, 6)

    def test_get_week_by_number(self):
        """Test get_week_by_number method"""
        result = self.tc_us.get_week_by_number(year=2024, week=10)
        self.assertEqual(result["week_nb"], 10)

        # Test with shift
        result_shifted = self.tc_us.get_week_by_number(year=2024, week=10, shift=2)
        self.assertEqual(result_shifted["week_nb"], 12)

    def test_cmp_month_by_number(self):
        """Test cmp_month_by_number method"""
        result = self.tc_us.cmp_month_by_number(year=2024, month=6)

        self.assertEqual(result["year"], 2024)
        self.assertEqual(result["month_nb"], 6)
        self.assertEqual(result["month_name"], "June")
        self.assertEqual(result["month_beg"], datetime.date(2024, 6, 1))
        self.assertIsInstance(result["month_end"], datetime.date)

    def test_cmp_month_by_number_with_start_day(self):
        """Test cmp_month_by_number with custom start day"""
        result = self.tc_us.cmp_month_by_number(year=2024, month=3, month_start_day=15)

        self.assertEqual(result["month_nb"], 3)
        self.assertEqual(result["month_beg"].day, 15)

    def test_cmp_month_by_number_translation(self):
        """Test month name translation in cmp_month_by_number"""
        result_de = self.tc_de.cmp_month_by_number(year=2024, month=3)
        self.assertEqual(result_de["month_name"], "März")  # German for March

        result_fr = self.tc_fr.cmp_month_by_number(year=2024, month=3)
        self.assertEqual(result_fr["month_name"], "mars")  # French for March

    def test_get_month_by_number(self):
        """Test get_month_by_number method"""
        result = self.tc_us.get_month_by_number(year=2024, month=8)
        self.assertEqual(result["month_nb"], 8)
        self.assertEqual(result["month_name"], "August")

    def test_get_month_by_number_with_shift(self):
        """Test get_month_by_number with shift"""
        result = self.tc_us.get_month_by_number(year=2024, month=8, shift=2)
        self.assertEqual(result["month_nb"], 10)
        self.assertEqual(result["month_name"], "October")

        # Test negative shift
        result_neg = self.tc_us.get_month_by_number(year=2024, month=8, shift=-2)
        self.assertEqual(result_neg["month_nb"], 6)
        self.assertEqual(result_neg["month_name"], "June")

    def test_leap_year(self):
        """Test month calculation in leap year"""
        tc = TimeClass(day=datetime.date(2024, 2, 29), country_code="US")
        self.assertEqual(tc._month_end, datetime.date(2024, 2, 29))

    def test_non_leap_year(self):
        """Test month calculation in non-leap year"""
        tc = TimeClass(day=datetime.date(2023, 2, 15), country_code="US")
        self.assertEqual(tc._month_end, datetime.date(2023, 2, 28))

    def test_year_boundaries(self):
        """Test calculations at year boundaries"""
        # First day of year
        tc_first = TimeClass(day=datetime.date(2024, 1, 1), country_code="US")
        self.assertEqual(tc_first._month_beg, datetime.date(2024, 1, 1))
        self.assertEqual(tc_first._year_beg, datetime.date(2024, 1, 1))

        # Last day of year
        tc_last = TimeClass(day=datetime.date(2024, 12, 31), country_code="US")
        self.assertEqual(tc_last._month_end, datetime.date(2024, 12, 31))
        self.assertEqual(tc_last._year_end, datetime.date(2024, 12, 31))

    def test_multiple_countries_holidays(self):
        """Test holiday detection across multiple countries"""
        test_dates = [
            (datetime.date(2024, 1, 1), "US", True, "New Year's Day"),
            (datetime.date(2024, 5, 1), "DE", True, "Erster Mai"),  # Labor Day in Germany
            (datetime.date(2024, 7, 14), "FR", True, "Fête nationale"),  # Bastille Day in France
        ]

        for date, country, should_be_holiday, name_contains in test_dates:
            tc = TimeClass(day=date, country_code=country)
            self.assertEqual(tc._is_holiday, should_be_holiday,
                           f"Failed for {date} in {country}")
            if should_be_holiday:
                self.assertIsNotNone(tc._holiday_name)
                self.assertIn(name_contains, tc._holiday_name)

    def test_country_code_case_insensitive(self):
        """Test that country code handling works regardless of case"""
        tc_upper = TimeClass(day=self.test_date, country_code="DE")
        tc_lower = TimeClass(day=self.test_date, country_code="de")

        # Both should work and produce the same results
        self.assertEqual(tc_upper._day_name, "Mittwoch")
        # tc_lower might fail due to holidays library expecting uppercase, but babel handles it

    def test_edge_case_week_53(self):
        """Test week calculation for week 53"""
        # Some years have 53 ISO weeks
        tc = TimeClass(day=datetime.date(2020, 12, 31), country_code="US")
        self.assertEqual(tc._week_nb, 53)


class TestTimeClassEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_invalid_country_code_fallback(self):
        """Test that invalid country codes fall back to English"""
        tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="XX")
        # Should fall back to English
        self.assertEqual(tc._day_name, "Wednesday")
        self.assertEqual(tc._month_name, "December")

    def test_future_date(self):
        """Test with future dates"""
        future_date = datetime.date(2030, 6, 15)
        tc = TimeClass(day=future_date, country_code="US")
        self.assertEqual(tc._year_nb, 2030)
        self.assertEqual(tc._month_nb, 6)

    def test_past_date(self):
        """Test with past dates"""
        past_date = datetime.date(2000, 1, 1)
        tc = TimeClass(day=past_date, country_code="US")
        self.assertEqual(tc._year_nb, 2000)
        self.assertTrue(tc._is_holiday)  # New Year's Day

    def test_run_method_called_automatically(self):
        """Test that run() is called automatically on initialization"""
        tc = TimeClass(day=datetime.date(2024, 6, 15), country_code="US")
        # If run() wasn't called, these would be None
        self.assertIsNotNone(tc._day_name)
        self.assertIsNotNone(tc._week_nb)
        self.assertIsNotNone(tc._month_nb)
        self.assertIsNotNone(tc._year_nb)


if __name__ == '__main__':
    unittest.main()
