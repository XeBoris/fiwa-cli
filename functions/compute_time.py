"""
Time computation utilities for date, week, month, and holiday calculations.

This module provides the TimeClass for comprehensive date and time calculations
with internationalization support for day names, month names, and holiday names
across different countries.

Features:
    - Day, week, month, and year calculations
    - ISO week number support
    - Holiday detection with translations
    - Multi-language support via Babel
    - Flexible date range calculations

Example:
    >>> from compute_time import TimeClass
    >>> import datetime
    >>>
    >>> # Create instance for German locale
    >>> tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="DE")
    >>> result = tc.get_day()
    >>> print(result['day_name'])  # 'Mittwoch'
    >>> print(result['holiday_name'])  # 'Weihnachten'
"""

import datetime
import time
import holidays
from babel.dates import format_date


class TimeClass:
    """
    A comprehensive time calculation class with internationalization support.

    This class provides methods for calculating and retrieving information about
    days, weeks, months, years, and holidays with support for multiple countries
    and languages.

    Attributes:
        _day (datetime.date): The reference date for all calculations.
        _country_code (str): ISO country code for locale-specific formatting.
        _day_name (str): Localized name of the day (e.g., 'Monday', 'Montag').
        _week_nb (int): ISO week number.
        _week_beg (datetime.date): Start date of the week (Monday).
        _week_end (datetime.date): End date of the week (Sunday).
        _month_nb (int): Month number (1-12).
        _month_name (str): Localized name of the month.
        _month_beg (datetime.date): First day of the month.
        _month_end (datetime.date): Last day of the month.
        _year_nb (int): Year number.
        _year_beg (datetime.date): First day of the year (January 1).
        _year_end (datetime.date): Last day of the year (December 31).
        _is_holiday (bool): Whether the current day is a holiday.
        _holiday_name (str or None): Localized name of the holiday.

    Example:
        >>> tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="FR")
        >>> tc._day_name
        'mercredi'
        >>> tc._holiday_name
        'Jour de Noël'
    """

    def __init__(self, day: datetime.date = datetime.date.today(), country_code: str = "US"):
        """
        Initialize TimeClass with a specific date and country code.

        Args:
            day (datetime.date, optional): The reference date for calculations.
                Defaults to today's date.
            country_code (str, optional): ISO country code (e.g., 'US', 'DE', 'FR')
                for locale-specific formatting. Defaults to 'US'.

        Example:
            >>> # Use today's date with US locale
            >>> tc = TimeClass()
            >>>
            >>> # Specific date with German locale
            >>> tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="DE")
        """
        self._day = day
        self._week_nb = None
        self._week_beg = None
        self._week_end = None
        self._month_nb = None
        self._month_beg = None
        self._month_end = None
        self._month_name = None
        self._country_code = country_code
        self.run()

    def run(self):
        """
        Execute all calculation methods to populate instance attributes.

        This method is called automatically during initialization and whenever
        the date or country code changes. It calculates day, week, month, year,
        and holiday information.

        Note:
            This method updates all instance attributes (_day_name, _week_nb, etc.)
        """
        self.cmp_day()
        self.cmp_week()
        self.cmp_month()
        self.cmp_year()
        self.cmp_holiday()

    def cmp_holiday(self):
        """
        Check if the current day is a holiday and get its localized name.

        This method uses the holidays library to detect holidays for the specified
        country and retrieves the holiday name in the local language.

        Sets:
            _is_holiday (bool): True if the current day is a holiday.
            _holiday_name (str or None): Localized name of the holiday, or None.

        Note:
            Falls back to US holidays if the specified country/language combination
            is not available. If that also fails, sets is_holiday to False.

        Example:
            >>> tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="DE")
            >>> tc.cmp_holiday()
            >>> tc._is_holiday
            True
            >>> tc._holiday_name
            'Weihnachten'
        """
        check_day = self._day

        try:
            # Get holidays with language parameter for translation
            # Map country code to language code (e.g., 'DE' -> 'de', 'FR' -> 'fr')
            language = self._country_code.lower()
            country_holidays = holidays.country_holidays(self._country_code, language=language)

            self._is_holiday = check_day in country_holidays
            self._holiday_name = country_holidays.get(check_day) if self._is_holiday else None
        except (NotImplementedError, KeyError):
            # Fallback to English if country/language not available
            try:
                country_holidays = holidays.country_holidays('US')
                self._is_holiday = check_day in country_holidays
                self._holiday_name = country_holidays.get(check_day) if self._is_holiday else None
            except:
                self._is_holiday = False
                self._holiday_name = None


    def get_day(self, day: datetime.date = None, country_code: str = None):
        """
        Get comprehensive date information for a specific day and locale.

        This method recalculates all date-related attributes for the specified
        day and country code, then returns them in a dictionary.

        Args:
            day (datetime.date, optional): The date to analyze. If None, uses
                today's date. Defaults to None.
            country_code (str, optional): ISO country code for localization.
                If None, uses the instance's current country code. Defaults to None.

        Returns:
            dict: A dictionary containing:
                - day (datetime.date): The reference date
                - day_name (str): Localized day name (e.g., 'Monday', 'Montag')
                - week_nb (int): ISO week number
                - week_beg (datetime.date): Start of the week (Monday)
                - week_end (datetime.date): End of the week (Sunday)
                - month_nb (int): Month number (1-12)
                - month_beg (datetime.date): First day of the month
                - month_end (datetime.date): Last day of the month
                - month_name (str): Localized month name (e.g., 'January', 'Januar')
                - year_nb (int): Year number
                - year_beg (datetime.date): First day of the year
                - year_end (datetime.date): Last day of the year
                - is_holiday (bool): Whether the day is a holiday
                - holiday_name (str or None): Localized holiday name

        Example:
            >>> tc = TimeClass(country_code="FR")
            >>> result = tc.get_day(datetime.date(2024, 7, 14))
            >>> result['day_name']
            'dimanche'
            >>> result['holiday_name']
            'Fête nationale'
        """
        self._day = day if day else datetime.date.today()
        self._country_code = country_code if country_code else self._country_code

        self.run()
        r = {
            "day": self._day,
            "day_name": self._day_name,
            "week_nb": self._week_nb,
            "week_beg": self._week_beg,
            "week_end": self._week_end,
            "month_nb": self._month_nb,
            "month_beg": self._month_beg,
            "month_end": self._month_end,
            "month_name": self._month_name,
            "year_nb": self._year_nb,
            "year_beg": self._year_beg,
            "year_end": self._year_end,
            "is_holiday": self._is_holiday,
            "holiday_name": self._holiday_name
        }
        return r

    def cmp_day(self):
        """
        Calculate and set the localized day name for the current date.

        Uses Babel for internationalization to translate the day name based
        on the country code. Falls back to English if the locale is not available.

        Sets:
            _day_name (str): Localized day name (e.g., 'Monday', 'Montag', 'lundi')

        Example:
            >>> tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="ES")
            >>> tc.cmp_day()
            >>> tc._day_name
            'miércoles'
        """
        # Map country codes to locale strings for babel
        locale_str = self._country_code.lower()  # 'US' -> 'us', 'DE' -> 'de'

        try:
            # Format day name in local language using babel
            self._day_name = format_date(self._day, format='EEEE', locale=locale_str)
        except:
            # Fallback to English if locale not available
            self._day_name = self._day.strftime("%A")

    def cmp_week(self):
        """
        Calculate ISO week number and week boundaries for the current date.

        Sets:
            _week_nb (int): ISO week number (1-53)
            _week_beg (datetime.date): Monday of the week
            _week_end (datetime.date): Sunday of the week

        Note:
            Uses ISO 8601 definition where weeks start on Monday and
            the first week of the year contains the first Thursday.

        Example:
            >>> tc = TimeClass(day=datetime.date(2024, 12, 25))
            >>> tc.cmp_week()
            >>> tc._week_nb
            52
        """
        self._week_nb = self._day.isocalendar()[1]
        self._week_beg = self._day - datetime.timedelta(days=self._day.weekday())
        self._week_end = self._week_beg + datetime.timedelta(days=6)

    def cmp_month(self):
        """
        Calculate month information and boundaries for the current date.

        Sets:
            _month_nb (int): Month number (1-12)
            _month_name (str): Localized month name (e.g., 'January', 'Januar')
            _month_beg (datetime.date): First day of the month
            _month_end (datetime.date): Last day of the month

        Note:
            Properly handles leap years and months with different day counts.

        Example:
            >>> tc = TimeClass(day=datetime.date(2024, 2, 15), country_code="DE")
            >>> tc.cmp_month()
            >>> tc._month_name
            'Februar'
            >>> tc._month_end
            datetime.date(2024, 2, 29)  # Leap year
        """
        self._month_nb = self._day.month

        # Translate month name based on country code
        locale_str = self._country_code.lower()
        try:
            self._month_name = format_date(self._day, format='MMMM', locale=locale_str)
        except:
            # Fallback to English
            self._month_name = self._day.strftime("%B")

        self._month_beg = self._day.replace(day=1)
        self._month_end = self._day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
        self._month_end = self._month_end - datetime.timedelta(days=self._month_end.day)

    def cmp_year(self):
        """
        Calculate year boundaries for the current date.

        Sets:
            _year_nb (int): Year number
            _year_beg (datetime.date): January 1 of the year
            _year_end (datetime.date): December 31 of the year

        Example:
            >>> tc = TimeClass(day=datetime.date(2024, 6, 15))
            >>> tc.cmp_year()
            >>> tc._year_nb
            2024
            >>> tc._year_beg
            datetime.date(2024, 1, 1)
        """
        self._year_nb = self._day.year
        self._year_beg = self._day.replace(month=1, day=1)
        self._year_end = self._day.replace(month=12, day=31)

    def cmp_week_by_number(self, year: int, week: int):
        """
        Calculate week boundaries for a specific ISO week number in a year.

        Args:
            year (int): The year for which to calculate the week
            week (int): ISO week number (1-53)

        Returns:
            dict: A dictionary containing:
                - year (int): The input year
                - week_nb (int): The input week number
                - week_beg (datetime.date): Start of the week (Monday)
                - week_end (datetime.date): End of the week (Sunday)

        Example:
            >>> tc = TimeClass()
            >>> result = tc.cmp_week_by_number(2024, 10)
            >>> result['week_beg']
            datetime.date(2024, 3, 4)
            >>> result['week_end']
            datetime.date(2024, 3, 10)
        """
        first_day_of_year = datetime.date(year, 1, 1)
        first_week_beg = first_day_of_year - datetime.timedelta(days=first_day_of_year.weekday())
        week_beg = first_week_beg + datetime.timedelta(weeks=week-1)
        week_end = week_beg + datetime.timedelta(days=6)

        r = {
            "year": year,
            "week_nb": week,
            "week_beg": week_beg,
            "week_end": week_end
        }

        return r

    def get_week_by_number(self, year: int, week: int, shift: int = 0):
        """
        Get week boundaries for a specific week with optional shift.

        This is a convenience method that allows shifting the week number
        forward or backward before calculation.

        Args:
            year (int): The year for which to calculate the week
            week (int): Base ISO week number (1-53)
            shift (int, optional): Number of weeks to shift (positive or negative).
                Defaults to 0.

        Returns:
            dict: Week information dictionary (see cmp_week_by_number)

        Example:
            >>> tc = TimeClass()
            >>> # Get week 10
            >>> result = tc.get_week_by_number(2024, 10)
            >>>
            >>> # Get week 12 (10 + 2)
            >>> result = tc.get_week_by_number(2024, 10, shift=2)
            >>> result['week_nb']
            12
        """
        return self.cmp_week_by_number(year, week + shift)

    def cmp_month_by_number(self, year: int, month: int, month_start_day: int = 1):
        """
        Calculate month boundaries for a specific month with custom start day.

        This method allows defining a custom start day for the month, which is
        useful for financial periods or custom accounting cycles.

        Args:
            year (int): The year
            month (int): Month number (1-12)
            month_start_day (int, optional): Day of month to start from (1-31).
                Defaults to 1.

        Returns:
            dict: A dictionary containing:
                - year (int): The input year
                - month_nb (int): The input month number
                - month_name (str): Localized month name
                - month_beg (datetime.date): Start date of the month period
                - month_end (datetime.date): End date of the month period

        Note:
            If month_start_day >= 15, the period spans from the start day in
            one month to the day before that date in the next month.

        Example:
            >>> tc = TimeClass(country_code="DE")
            >>> # Standard month (1st to last day)
            >>> result = tc.cmp_month_by_number(2024, 3, month_start_day=1)
            >>> result['month_name']
            'März'
            >>>
            >>> # Custom period (15th to 14th of next month)
            >>> result = tc.cmp_month_by_number(2024, 3, month_start_day=15)
            >>> result['month_beg']
            datetime.date(2024, 3, 15)
            >>> result['month_end']
            datetime.date(2024, 4, 15)
        """
        month_beg = datetime.date(year, month, month_start_day)

        # Translate month name based on country code
        locale_str = self._country_code.lower()
        try:
            month_name = format_date(month_beg, format='MMMM', locale=locale_str)
        except:
            # Fallback to English
            month_name = month_beg.strftime("%B")

        if month_start_day >= 15:
            month_beg = month_beg - datetime.timedelta(days=month_start_day)
            month_beg = month_beg.replace(day=month_start_day)
            month_end = month_beg.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
            month_end = month_end.replace(day=month_start_day)
        else:
            #month_beg = month_beg - datetime.timedelta(days=month_start_day)
            #month_beg = month_beg.replace(day=month_start_day)
            month_end = month_beg.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
            month_end = month_end.replace(day=month_start_day)

        r = {
            "year": year,
            "month_beg": month_beg,
            "month_end": month_end,
            "month_nb": month,
            "month_name": month_name
        }
        return r

    def get_month_by_number(self, year: int, month: int, month_start_day: int = 1, shift: int = 0):
        """
        Get month boundaries with optional month shift.

        This is a convenience method that allows shifting the month number
        forward or backward before calculation.

        Args:
            year (int): The year
            month (int): Base month number (1-12)
            month_start_day (int, optional): Day of month to start from. Defaults to 1.
            shift (int, optional): Number of months to shift (positive or negative).
                Defaults to 0.

        Returns:
            dict: Month information dictionary (see cmp_month_by_number)

        Example:
            >>> tc = TimeClass(country_code="FR")
            >>> # Get March
            >>> result = tc.get_month_by_number(2024, 3)
            >>> result['month_name']
            'mars'
            >>>
            >>> # Get May (March + 2)
            >>> result = tc.get_month_by_number(2024, 3, shift=2)
            >>> result['month_nb']
            5
            >>> result['month_name']
            'mai'
        """
        return self.cmp_month_by_number(year, month + shift, month_start_day=month_start_day)