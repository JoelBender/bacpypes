#!/usr/bin/env python

from bacpypes.primitivedata import Date

year_group = ('04', '75', '1929', '255', '*')
month_group = ('1', '12', 'odd', 'even', '255', '*')
day_group = ('1', '22', 'last', 'odd', 'even', '255', '*')
dow_group = ('1', 'mon', '255', '*')

patterns = [
    "%(year)s-%(month)s-%(day)s %(day_of_week)s",
    "%(month)s/%(day)s/%(year)s %(day_of_week)s",
    "%(day)s/%(month)s/%(year)s %(day_of_week)s",
    ]

def permutation(**kwargs):
    for pattern in patterns:
        test_string = pattern % kwargs
        try:
            test_date = Date(test_string)
            test_value = test_date.value
        except Exception as why:
            test_value = str(why)
        print(test_string + '\t' + str(test_value))
    print("")

for year in year_group:
    for month in month_group:
        for day in day_group:
            for day_of_week in dow_group:
                permutation(
                    year=year, month=month, day=day, day_of_week=day_of_week,
                    )
