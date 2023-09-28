import math
import os
from datetime import datetime
from typing import List

from classes import Stage
from main import process_loadshedding, to_datetime

ZONE = 3
ESKOM = False


def main():
    # zone is 3
    # call loadshedding with zone
    data = process_loadshedding(ZONE, ESKOM)
    time_now = datetime.combine(datetime.today(), datetime.min.time())
    geyser_start = time_now.replace(hour=16, minute=0, second=0, microsecond=0)
    geyser_end = time_now.replace(hour=17, minute=0, second=0, microsecond=0)

    # get for today
    todays = [day["stages"] for day in data["load_shedding"] if day["date"] == time_now.date()]
    if len(todays) > 0:
        today_stages = todays[0]
        # check for stage within 4-5pm
        geyser_matches: List[Stage] = [stage for stage in today_stages if
                                       stage.start_time <= geyser_start and stage.end_time >= geyser_end]
        if len(geyser_matches) > 0:
            # realign geyser times
            # hour before geyser match
            geyser_start = time_now.replace(hour=geyser_matches[0].start_time.hour - 1)
            geyser_end = time_now.replace(hour=geyser_matches[0].start_time.hour)

    # do geyser stuff
    if geyser_start.hour == 16:
        # do nothing, already correct
        print("skipping - schedule is correct")
    else:
        if geyser_start <= datetime.now():
            # do stuff
            if datetime.now() <= geyser_end:
                os.system("node ~/internal/src/sboothza/ewelink/set_geyser.js on")
            else:
                os.system("node ~/internal/src/sboothza/ewelink/set_geyser.js off")
        else:
            print("Schedule needs to be manually updated - run again closer to the time - {:%H:%M} to {:%H:%M}".format(geyser_start, geyser_end))


if __name__ == '__main__':
    main()
