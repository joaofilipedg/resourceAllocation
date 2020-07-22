import logging

from flask_app.app import db
from flask_app.src.models import User, Host, Component, Reservation_type, Reservation
from flask_app.src.global_stuff import DEBUG_MODE

from flask_app.src.models.sql_query import get_listReservationsHost

# Function activated by the scheduler when END Time of a reservation activates

# Function to check if a new reservation conflicts with any of the previous ones
# (Return True if there is a conflict)
def check_conflictsNewReservation(new_res, log_args={}):    
    list_res = get_listReservationsHost(new_res["hostID"], log_args=log_args)

    for res in list_res:
        # Check if there is any intersection of the timeslot
        if (new_res["end_date"] <= res["begin_date"]) or (new_res["begin_date"] >= res["end_date"]):
            continue
        else:
            # if there is, need to check if the reservation types results in conflicts or not

            # Uncomment to debug
            # print("\tPossible conflict (Time is conflicting with res {})".format(res[0]))
            # print("\tres: '{}'".format(res))
            # print("\tnew_res: '{}'".format(new_res))
            # print("\t\tres[res_type]: '{}'".format(res[IDX_RESTYPE]))
            # print("\t\tnew_res[res_type]: '{}'".format(new_res["res_type"]))

            # if either of the reservations (old conflicting one or new one) is of type 1 (RESERVED FULL)
            # conflict_res = "<br/><br/>Conflicting reservation (reservationID, username, hostname, reservation_type, begin_date, end_date):<br/>    {}".format(res)
            conflict_res = " Conflicting reservation (reservationID, username, hostname, reservation_type, begin_date, end_date): {}".format(res)
            if (res["reservation_type"] == 1) or (int(new_res["res_type"]) == 1):
                error_str = "New reservation conflicts with existing reservation. (One of them is of type 'RESERVED FULL SYSTEM')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            
            # if both reservations (old conflicting one and new one) are locking the FPGA (RESERVED FPGA)
            if (res["reservation_type"] == 2) and (int(new_res["res_type"]) == 2):
                error_str = "New reservation conflicts with existing reservation. (Both of them are of type 'RESERVED FPGA')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            
            # if both reservations (old conflicting one and new one) are locking the GPU (RESERVED GPU)
            if (res["reservation_type"] == 3) and (int(new_res["res_type"]) == 3):
                error_str = "New reservation conflicts with existing reservation. (Both of them are of type 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res

            # if old res is RESERVED_GPU or RESERVED_FPGA and new one is DEVELOPING or RUNNING PROGRAMS
            if ((res["reservation_type"] == 2) or (res["reservation_type"] == 3)) and ((int(new_res["res_type"]) == 4) or (int(new_res["res_type"]) == 5)):
                error_str = "New reservation conflicts with existing reservation. (New reservation is of type 'DEVELOPING' or 'RUNNING PROGRAMS/SIMULATIONS', which conflicts with reservations of type 'RESERVED FPGA' or 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res

            # if old res is DEVELOPING or RUNNING PROGRAMS and new one is RESERVED_GPU or RESERVED_FPGA 
            if ((res["reservation_type"] == 4) or (res["reservation_type"] == 5)) and ((int(new_res["res_type"]) == 2) or (int(new_res["res_type"]) == 3)):
                error_str = "New reservation conflicts with existing reservation. (Existing reservation is of type 'DEVELOPING' or 'RUNNING PROGRAMS/SIMULATIONS', which conflicts with new reservation of type 'RESERVED FPGA' or 'RESERVED GPU')"
                print("\t{}".format(error_str))
                return True, error_str+conflict_res
            # if 

    return False, ""

def check_hostStatusNextWeek(hostID, log_args={}):
    from datetime import datetime, timedelta
    
    next_week = [0] * 7 # one field for each day of the next week. 0-free, 1-reserved full, 2-reserved fpga, 3-reserved gpu, 4-running programs, 5-developing, 6-reserved gpu and fpga
    
    time_now = datetime.now()
    current_day = time_now.strftime("%Y-%m-%d")
    time_in_one_week = time_now + timedelta(days=7)
    nextweek_day = time_in_one_week.strftime("%Y-%m-%d")
    print(current_day)
    print(nextweek_day)

    list_res = get_listReservationsHost(hostID, log_args=log_args)
    for res in list_res:
        # check if reservation falls into the next week
        if (res["begin_date"] >= nextweek_day) or (res["end_date"] <= current_day):
            continue

        # if it reaches here there is already some days where the host is in use during the next week
        day_aux = time_now
        for day_i in range(0,7):
            str_day_aux = day_aux.strftime("%Y-%m-%d")
            day_aux += timedelta(days=1)
            
            if next_week[day_i] == 1:
                continue     

            if (str_day_aux >= res["begin_date"]) and (str_day_aux <= res["end_date"]):
                
                if next_week[day_i] == 0:
                    # if day was still assigned as free
                    next_week[day_i] = res["reservation_type"]
                
                elif ((next_week[day_i] == 2) and (res["reservation_type"] == 3)) or ((next_week[day_i] == 3) and (res["reservation_type"] == 2)):
                    # if day has GPU and FPGA reserved
                    next_week[day_i] = 6

                elif next_week[day_i] == 7:
                    # if day already had GPU and FPGA reserved only allow CPU reserved
                    if (res["reservation_type"] == 1): 
                        next_week[day_i] = 1

                elif next_week[day_i] < res["reservation_type"]:
                    # if day still had lower priority than this reservation
                    next_week[day_i] = res["reservation_type"]
             
        if next_week == [1] * 7:
            # this would be already the worst case scenario, no point in continuing through the reservations
            break

    return next_week