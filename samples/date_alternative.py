#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time

from bacpypes.primitivedata import Tag, Atomic

_mm = r'(?P<month>0?\d|1[0-4]|odd|even|255|[*])'
_dd = r'(?P<day>[0-3]?\d|last|odd|even|255|[*])'
_yy = r'(?P<year>\d{2}|255|[*])'
_yyyy = r'(?P<year>\d{4}|255|[*])'
_dow = r'(?P<dow>[1-7]|mon|tue|wed|thu|fri|sat|sun|255|[*])'

_special_mon = {'*': 255, 'odd': 13, 'even': 14, None: 255}
_special_mon_inv = {255: '*', 13: 'odd', 14: 'even'}

_special_day = {'*': 255, 'last': 32, 'odd': 33, 'even': 34, None: 255}
_special_day_inv = {255: '*', 32: 'last', 33: 'odd', 34: 'even'}

_special_dow = {'*': 255, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 7}
_special_dow_inv = {255: '*', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat', 7: 'sun'}


def _merge(*args):
    """Create a composite pattern and compile it."""
    return re.compile(r'^' + r'[/-]'.join(args) + r'(?:\s+' + _dow + ')?$')


# make a list of compiled patterns
_date_patterns = [
    _merge(_yyyy, _mm, _dd),
    _merge(_mm, _dd, _yyyy),
    _merge(_dd, _mm, _yyyy),
    _merge(_yy, _mm, _dd),
    _merge(_mm, _dd, _yy),
    _merge(_dd, _mm, _yy),
    ]


class Date(Atomic):

    def __init__(self, arg=None, year=255, month=255, day=255, day_of_week=255):
        self.value = (year, month, day, day_of_week)
        
        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, tuple):
            self.value = arg
        elif isinstance(arg, str):
            # lower case everything
            arg = arg.lower()

            # make a list of the contents from matching patterns
            matches = []
            for p in _date_patterns:
                m = p.match(arg)
                if m:
                    matches.append(m.groupdict())

            # try to find a good one
            match = None
            if not matches:
                raise ValueError("unmatched")

            # if there is only one, success
            if len(matches) == 1:
                match = matches[0]
            else:
                # check to see if they really are the same
                for a, b in zip(matches[:-1],matches[1:]):
                    if a != b:
                        raise ValueError("ambiguous")
                        break
                else:
                    match = matches[0]

            # extract the year and normalize
            year = match['year']
            if (year == '*') or (not year):
                year = 255
            else:
                year = int(year)
                if (year == 255):
                    pass
                elif year < 35:
                    year += 2000
                elif year < 100:
                    year += 1900

            # extract the month and normalize
            month = match['month']
            if month in _special_mon:
                month = _special_mon[month]
            else:
                month = int(month)
                if month > 14:
                    print("invalid month")

            # extract the day and normalize
            day = match['day']
            if day in _special_day:
                day = _special_day[day]
            else:
                day = int(day)
                if day > 34:
                    print("invalid day")

            # extract the day-of-week and normalize
            day_of_week = match['dow']
            if day_of_week in _special_dow:
                day_of_week = _special_dow[day_of_week]
            elif not day_of_week:
                pass
            else:
                day_of_week = int(day_of_week)

            # year becomes the correct octet
            if year != 255:
                year -= 1900

            # save the value
            self.value = (year, month, day, day_of_week)

            # calculate the day of the week
            if not day_of_week:
                self.CalcDayOfWeek()

        elif isinstance(arg, Date):
            self.value = arg.value

        else:
            raise TypeError("invalid constructor datatype")

    def CalcDayOfWeek(self):
        """Calculate the correct day of the week."""
        # rip apart the value
        year, month, day, day_of_week = self.value

        # assume the worst
        day_of_week = 255

        # check for special values
        if year == 255:
            pass
        elif month in _special_mon_inv:
            pass
        elif day in _special_day_inv:
            pass
        else:
            try:            
                today = time.mktime( (year + 1900, month, day, 0, 0, 0, 0, 0, -1) )
                day_of_week = time.gmtime(today)[6] + 1
            except OverflowError:
                pass

        # put it back together
        self.value = (year, month, day, day_of_week)

    def now(self):
        tup = time.localtime()
        self.value = (tup[0]-1900, tup[1], tup[2], tup[6] + 1)
        return self

    def encode(self, tag):
        # encode the tag
        tag.set_app_data(Tag.dateAppTag, bytearray(self.value))

    def decode(self, tag):
        if (tag.tagClass != Tag.applicationTagClass) or (tag.tagNumber != Tag.dateAppTag):
            raise ValueError("date application tag required")

        # rip apart the data
        self.value = tuple(tag.tagData)

    def __str__(self):
        """String representation of the date."""
        # rip it apart
        year, month, day, day_of_week = self.value

        if year == 255:
            year = "*"
        else:
            year = str(year + 1900)

        month = _special_mon_inv.get(month, str(month))
        day = _special_day_inv.get(day, str(day))
        day_of_week = _special_dow_inv.get(day_of_week, str(day_of_week))

        return "%s-%s-%s %s" % (year, month, day, day_of_week)

    def __repr__(self):
        return "<%s(%s) at 0x%x>" % (self.__class__.__name__, str(self), id(self))
