import argparse
import copy
import datetime
import json
import os.path
import re
import urllib
from pathlib import Path
from typing import Optional, List

import dateutil.parser
import requests
import tabula
import collections

import eskom_config
from classes import Stage, ZoneStageByDay, ZoneStageMap, stage_sort
from extensions import Lst

collections.Callable = collections.abc.Callable

from bs4 import BeautifulSoup

from schedule_config import area_schedule
from serializer import serializer_instance

schedules: List[Stage] = []


def get_fullname(path: str) -> str:
    p = Path(path)
    p.resolve()
    return str(p.expanduser())


def replace_all(text: str, search: str, replace: str) -> str:
    while text.find(search) > -1:
        text = text.replace(search, replace)
    return text


def get_line(text: str):
    pos = text.find("\n")
    if pos > -1:
        line = text[:pos].strip()
        text = text[pos + 1:]
        return line, text
    return "", text


def find_line(text: str, match: str):
    line = "xxxxxxxxxxxxxx"
    while not line.startswith(match):
        if text == "":
            return False, text
        line, text = get_line(text)
    return True, text


static_zones = ZoneStageMap()


def process_static_zones(stage: int, day_group: str, start_time: datetime.datetime, end_time: datetime.datetime,
                         zone_list: List[str]):
    start_day = 0
    max_day = 0

    if day_group == "1-16,17-31":
        start_day = 1
        max_day = 17
    elif day_group == "1-8,17-24":
        start_day = 1
        max_day = 9
    elif day_group == "9-16,25-31":
        start_day = 9
        max_day = 17

    for day in range(start_day, max_day):
        zones_for_day = [int(x) for x in re.split(r"\W+", zone_list[(day - start_day)].strip())]
        zone_stage = ZoneStageByDay(stage, start_time, end_time, zones_for_day)
        static_zones.add_zone_stage(day, zone_stage)
        static_zones.add_zone_stage(day + 16, zone_stage)


def to_datetime(value: str, default: datetime.datetime = datetime.datetime.min) -> datetime.datetime:
    return dateutil.parser.parse(value, default=default)


def process_static_schedule():
    for area_schedule_item in area_schedule:
        stage = int(area_schedule_item['Stage'])
        date_range = area_schedule_item['Dates']

        for zone in area_schedule_item['Zones']:
            matches = re.search(r"(\d+:\d{2}) (\d+:\d{2})", zone[0])

            if matches:
                process_static_zones(stage, date_range, to_datetime(matches.group(1)), to_datetime(matches.group(2)),
                                     zone[1:])

            else:
                print("Error!")
                exit(0)


def download_file(url: str, filename: str):
    urllib.request.urlretrieve(url, filename)


def isNaN(num):
    return num != num


def process_raw_row(row, max_zones):
    new_row = []
    first = None
    for value in row:
        if isNaN(value):
            pass
        elif re.search(r"(\d+:\d{2}) (\d+:\d{2})", value):
            new_row.append(value)
        elif re.search(r"(\d+:\d{2})", value):
            if first is None:
                first = value
            else:
                new_row.append("{} {}".format(first, value))
                first = None
        else:
            z = re.split(r"\W+", value)
            while len(z) > 0:
                new_value = ",".join(z[0:max_zones])
                new_row.append(new_value)
                z = z[max_zones:]
    return new_row


def process_stage_1_2(values, schedule):
    stage = {'Stage': '1', 'Dates': '1-16,17-31', 'Zones': []}
    for row in range(4, 16):
        stage["Zones"].append(process_raw_row(values[row], 1))

    schedule.append(stage)
    stage = {'Stage': '2', 'Dates': '1-16,17-31', 'Zones': []}
    for row in range(21, 33):
        stage["Zones"].append(process_raw_row(values[row], 2))
    schedule.append(stage)


def process_stage_3_4(values, schedule):
    stage = {'Stage': '3', 'Dates': '1-16,17-31', 'Zones': []}
    for row in range(4, 16):
        stage["Zones"].append(process_raw_row(values[row], 3))

    schedule.append(stage)
    stage = {'Stage': '4', 'Dates': '1-16,17-31', 'Zones': []}
    for row in range(21, 33):
        stage["Zones"].append(process_raw_row(values[row], 4))
    schedule.append(stage)


def process_stage_5(values, schedule):
    stage = {'Stage': '5', 'Dates': '1-8,17-24', 'Zones': []}
    for row in range(4, 16):
        stage["Zones"].append(process_raw_row(values[row], 5))

    schedule.append(stage)
    stage = {'Stage': '5', 'Dates': '9-16,25-31', 'Zones': []}
    for row in range(20, 32):
        stage["Zones"].append(process_raw_row(values[row], 5))
    schedule.append(stage)


def process_stage_6(values, schedule):
    stage = {'Stage': '6', 'Dates': '1-8,17-24', 'Zones': []}
    for row in range(4, 16):
        stage["Zones"].append(process_raw_row(values[row], 6))

    schedule.append(stage)
    stage = {'Stage': '6', 'Dates': '9-16,25-31', 'Zones': []}
    for row in range(20, 32):
        stage["Zones"].append(process_raw_row(values[row], 6))
    schedule.append(stage)


def process_stage_7(values, schedule):
    stage = {'Stage': '7', 'Dates': '1-8,17-24', 'Zones': []}
    for row in range(4, 16):
        stage["Zones"].append(process_raw_row(values[row], 7))

    schedule.append(stage)
    stage = {'Stage': '7', 'Dates': '9-16,25-31', 'Zones': []}
    for row in range(20, 32):
        stage["Zones"].append(process_raw_row(values[row], 7))
    schedule.append(stage)


def process_stage_8_1(values, schedule):
    stage = {'Stage': '8', 'Dates': '1-8,17-24', 'Zones': []}
    for row in range(2, 14):
        stage["Zones"].append(process_raw_row(values[row], 8))

    schedule.append(stage)


def process_stage_8_2(values, schedule):
    stage = {'Stage': '8', 'Dates': '9-16,25-31', 'Zones': []}
    for row in range(2, 14):
        stage["Zones"].append(process_raw_row(values[row], 8))

    if len(stage["Zones"][11]) == 8:
        # stuffing thing misses the last cell...
        temp = stage["Zones"][11][7]
        stage["Zones"][11].append(temp)
    schedule.append(stage)


def download_table():
    url = "https://www.capetown.gov.za/Loadshedding1/loadshedding/Load_Shedding_All_Areas_Schedule_and_Map.pdf"

    path = os.path.join(os.getcwd(), "Load_Shedding_All_Areas_Schedule_and_Map.pdf")
    path = get_fullname(path)
    if not os.path.exists(path):
        download_file(url, path)

    new_schedule = []
    tables = tabula.read_pdf(path, pages="2", multiple_tables=True, guess=False)
    process_stage_1_2(tables[0].values, new_schedule)
    tables = tabula.read_pdf(path, pages="3", multiple_tables=True, guess=False)
    process_stage_3_4(tables[0].values, new_schedule)
    tables = tabula.read_pdf(path, pages="4", multiple_tables=True, guess=False)
    process_stage_5(tables[0].values, new_schedule)
    tables = tabula.read_pdf(path, pages="5", multiple_tables=True, guess=False)
    process_stage_6(tables[0].values, new_schedule)
    tables = tabula.read_pdf(path, pages="6", multiple_tables=True, guess=False)
    process_stage_7(tables[0].values, new_schedule)
    tables = tabula.read_pdf(path, pages="7", multiple_tables=True, guess=False)
    process_stage_8_1(tables[0].values, new_schedule)
    process_stage_8_2(tables[1].values, new_schedule)

    text = serializer_instance.serialize(new_schedule)
    path = os.path.join(os.getcwd(), "src", "schedule_config.py")
    with open(path, 'w') as output_file:
        output_file.write("area_schedule = " + text)
        output_file.flush()


def load_schedule_from_web():
    page = requests.get(
        "https://www.capetown.gov.za/Family%20and%20home/Residential-utility-services/Residential-electricity-services/Load-shedding-and-outages")
    soup = BeautifulSoup(page.content, "html5lib")
    tags = soup.find_all("div", class_="section-pull")
    text = tags[0].text
    text = replace_all(text, "\r", "")
    text = replace_all(text, "\t", "")
    text = replace_all(text, "\n\n", "\n")
    text = match_current_schedule_header(text)
    text = match_current_schedule_dates_and_update(text)


def split_current_schedules():
    global schedules
    new_schedules: List[Stage] = []
    for schedule in schedules:
        if schedule.end_time.day == schedule.start_time.day:
            new_schedules.append(schedule)
        else:
            # multiple days
            day: int = schedule.start_time.day
            new_start_date = schedule.start_time
            new_end_date = datetime.datetime.combine(schedule.start_time, datetime.time.max)
            while True:
                s = Stage(schedule.number, new_start_date, new_end_date)
                new_schedules.append(s)
                day = day + 1
                new_start_date = new_start_date.replace(day=day, hour=0, minute=0, second=0, microsecond=0)
                if new_start_date > schedule.end_time:
                    break

                new_end_date = new_end_date.replace(day=day)
                if new_end_date > schedule.end_time:
                    new_end_date = schedule.end_time

    schedules = new_schedules


def merge_stages(stages: List[Stage]):
    if len(stages) < 2:
        return stages

    cleaned_stages: Lst[Stage] = Lst(stages)

    i: int = 0
    while i < len(cleaned_stages) - 1:
        stage1 = cleaned_stages[i]
        stage2 = cleaned_stages[i + 1]
        if stage2.start_time <= stage1.end_time:
            new_stage: Stage = copy.deepcopy(stage1)
            new_stage.end_time = stage2.end_time
            cleaned_stages.remove(stage1)
            cleaned_stages.remove(stage2)
            cleaned_stages.insert(i, new_stage)
        else:
            i = i + 1

    return cleaned_stages


# compare next if there is one


def main():
    global schedules
    parser = argparse.ArgumentParser(description="Download videos from streaming source")
    parser.add_argument('--zone',
                        help='zone',
                        dest='zone',
                        type=int,
                        default=0,
                        required=False)
    parser.add_argument('--update-tables',
                        help='Update zone tables',
                        dest='update',
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument('--use-eskom',
                        help='Use Eskom schedule',
                        dest='eskom',
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument('--json',
                        help='Json output',
                        dest='json',
                        action='store_true',
                        default=False,
                        required=False)

    args = parser.parse_args()

    if args.update:
        download_table()
        exit(0)

    if args.zone == 0:
        print('Zone is required')
        parser.print_help()
        exit(1)

    process_static_schedule()
    my_zone = int(args.zone)
    time_now = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

    if args.eskom:
        schedules = serializer_instance.remap(eskom_config.eskom_schedules)
    else:
        # schedules = serializer_instance.remap(
        #     [{"number": 3, "start_time": "2023-01-27 00:00:00", "end_time": "2023-01-27 22:00:00"},
        #      {"number": 4, "start_time": "2023-01-27 22:00:00", "end_time": "2023-01-30 00:00:00"}])
        load_schedule_from_web()

    for static_stage in schedules:
        if static_stage.end_time <= static_stage.start_time:
            static_stage.end_time = static_stage.end_time + datetime.timedelta(days=1)

    split_current_schedules()
    # find times for zone from start time to end time

    active_schedules = [s for s in schedules if time_now <= s.end_time]

    new_stages = []
    for schedule in active_schedules:
        # find zone schedule that falls in this schedule
        stages_for_today = static_zones.get_for_day_and_zone(schedule.end_time.day, my_zone,
                                                             schedule.start_time.date(),
                                                             schedule.number)

        for static_stage in stages_for_today:
            if schedule.start_time <= static_stage.start_time and schedule.end_time >= static_stage.end_time:
                # check for existing
                existing = [x for x in new_stages if
                            x.start_time == static_stage.start_time and x.end_time == static_stage.end_time]
                if len(existing) == 0:
                    new_stages.append(static_stage)

    new_stages = merge_stages(new_stages)

    # print("Live schedules:")
    # for sched in schedules:
    #     print(sched)

    new_stages.sort(key=lambda x: x.start_time, reverse=False)

    if args.json:
        combined = {"calculation_date": datetime.datetime.now(), "schedules": schedules, "load_shedding": []}
        current_date = datetime.datetime.min

        current_stage = None
        for static_stage in new_stages:
            d = static_stage.start_time.date()
            if d != current_date:
                if current_stage is not None:
                    combined["load_shedding"].append(current_stage)

                    current_stage = {"display_date": "{:%A, %B %d}".format(d), "date": d, "stages": []}
                    current_date = d
                    current_stage["stages"].append(static_stage)

        print(serializer_instance.serialize(combined, pretty=True))
    else:
        print("Current loadshedding status for zone {}".format(my_zone))
        # new_stages.sort(key=stage_sort)

        current_date = datetime.datetime.min
        for static_stage in new_stages:
            d = static_stage.start_time.date()
            if d != current_date:
                print("{:%A, %B %d}".format(d))
                current_date = d
            print(static_stage.disp())


def match_current_schedule_header(text):
    res, text = find_line(text, "Load-shedding")
    if not res:
        print("fail")
        exit(0)
    res, text = find_line(text, "City customers:")
    if not res:
        print("fail")
        exit(0)
    return text


def parse_stage(line, stage_date) -> Optional[Stage]:
    regex = r"Stage (\d+): (\d{2}:\d{2}) - (\d{2}:\d{2})"
    matches = re.search(regex, line)

    if matches:
        stage = Stage(int(matches.group(1)), to_datetime(matches.group(2), stage_date),
                      to_datetime(matches.group(3), stage_date))
        if stage.end_time < stage.start_time:
            stage.end_time = stage.end_time + datetime.timedelta(days=1)
        return stage
    else:
        regex = r"Stage (\d+):.*?(\d{2}:\d{2})"
        matches = re.search(regex, line)
        if matches:
            stage = Stage(int(matches.group(1)), datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()),
                          to_datetime(matches.group(2), stage_date))
            if stage.end_time < stage.start_time:
                stage.end_time = stage.end_time + datetime.timedelta(days=1)
            return stage
    return None


def match_current_schedule_dates_and_update(text):
    global schedules

    state = "date"  # stage, other
    line, text = get_line(text)
    date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
    while state != "other":
        if state == "date":
            if line.startswith('Stage'):
                state = "stage"
            else:
                try:
                    date = dateutil.parser.parse(line)
                    state = "stage"
                    line, text = get_line(text)
                except:
                    if line.startswith("Stage"):
                        state = "stage"
                    else:
                        state = "other"
        elif state == "stage":
            if line.startswith("Stage"):
                stage = parse_stage(line, date)
                schedules.append(stage)
                line, text = get_line(text)
            else:
                state = "date"

    return text


if __name__ == '__main__':
    main()
