import copy
import datetime
from typing import Optional, List

from extensions import get_date, Lst
from serializer import serializer_instance


class Stage:
    """Both static and dynamic stage information"""

    def __init__(self, stage: int = 0, start_time: datetime.datetime = datetime.datetime.min,
                 end_time: datetime.datetime = datetime.datetime.min):
        self.number: int = stage
        self.start_time: datetime.datetime = start_time
        self.end_time: datetime.datetime = end_time
        self.key = self._make_key()

    def _make_key(self):
        return "{:00}-{}".format(self.number, str(self.start_time))

    def __str__(self):
        return "Stage:{} from:{} to {}".format(self.number, self.start_time, self.end_time)

    def load(self, obj, serializer):
        self.number = int(obj["number"])
        self.start_time = get_date(obj["start_time"])
        self.end_time = get_date(obj["end_time"])
        self.key = self._make_key()

    def disp(self):
        return "{:%H:%M} to {:%H:%M} : Stage {}".format(self.start_time, self.end_time, self.number)


def stage_sort(s: Stage):
    return s.key


def merge_all_stages(stages: List[Stage]):
    if len(stages) < 2:
        return stages

    cleaned_stages: Lst[Stage] = Lst(stages)

    i: int = 0
    while i < len(cleaned_stages) - 1:
        stage1 = cleaned_stages[i]
        stage2 = cleaned_stages[i + 1]
        if stage2.start_time <= stage1.end_time and stage2.number == stage1.number:
            new_stage: Stage = copy.deepcopy(stage1)
            new_stage.end_time = stage2.end_time
            cleaned_stages.remove(stage1)
            cleaned_stages.remove(stage2)
            cleaned_stages.insert(i, new_stage)
        else:
            i = i + 1

    return cleaned_stages


serializer_instance.register(Stage(), "end_time:number:start_time")


# class AreaScheduleMap:
#     def __init__(self, stage: int = 0, day_group: str = '', start_time: datetime.datetime = datetime.datetime.min,
#                  end_time: datetime.datetime = datetime.datetime.min, zone_list=None):
#         if zone_list is None:
#             zone_list = []
#         self.stage: int = stage
#         self.day_group: str = day_group
#         self.start_time: datetime.datetime = start_time
#         self.end_time: datetime.datetime = end_time
#         self.zone_list = zone_list
#
#     def __str__(self):
#         return "Stage:{} day_group:{} start:{} end:{} zones:{}".format(self.stage, self.day_group, self.start_time,
#                                                                        self.end_time, self.zone_list)
#
#
# serializer_instance.register(AreaScheduleMap())


class ZoneStageByDay:
    """Static stage information for a day"""

    def __init__(self, stage: int = 0, start_time: datetime.datetime = datetime.datetime.min,
                 end_time: datetime.datetime = datetime.datetime.min, zone_list: Optional[List[int]] = None):
        self.stage = stage
        if zone_list is None:
            zone_list = []
        self.start_time = start_time
        self.end_time = end_time
        self.zone_list = zone_list

    def __str__(self):
        return "stage:{} start:{} end:{} zones:[{}]".format(self.stage, self.start_time, self.end_time,
                                                            ",".join([str(z) for z in self.zone_list]))


serializer_instance.register(ZoneStageByDay())


class ZoneStageMap:
    def __init__(self):
        self.stage_by_day = {}

    def add_zone_stage(self, day: int, zone: ZoneStageByDay):
        stages = None
        if day not in self.stage_by_day:
            stages = []
        else:
            stages = self.stage_by_day[day]

        stages.append(zone)
        self.stage_by_day[day] = stages

    def get_for_day_and_zone(self, day: int, zone: int, for_date: datetime.datetime, stage: int):
        day_schedules = self.stage_by_day[day]
        new_list = [Stage(zs.stage, datetime.datetime.combine(for_date, zs.start_time.time()),
                          datetime.datetime.combine(for_date, zs.end_time.time())) for zs in day_schedules
                    if zone in zs.zone_list and zs.stage <= stage]
        new_list.sort(key=stage_sort)

        new_list = merge_all_stages(new_list)
        return new_list


serializer_instance.register(ZoneStageMap())
