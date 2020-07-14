function changeHostSelected(host) {
    var sel = document.getElementById('host');
    var opts = sel.options;
    for (var opt, j = 0; opt = opts[j]; j++) {
        if (opt.value == host) {
            sel.selectedIndex = j;
            break;
        }
    }
}

// verify that reservation is valid before sending request to server
function verifyReservation() {
    var user = document.forms["new_res_form"]["username"].value;
    if (user == "") {
        alert("Username must be filled out.");
        return false;
    } else {
        var host = document.forms["new_res_form"]["host"].value;
        if (host === "") {
            alert("Please select an host.");
            return false;
        } else {
            var res_type = document.forms["new_res_form"]["res_type"].value;
            if (res_type === "") {
                alert("Please select a reservation type.");
                return false;
            } else {
                document.getElementById("username").disabled = false;
                return true;
            }
        }        
    }
}

function cancelReservation(res_id) {
    var sure = window.confirm("Are you sure you want to cancel this reservation?");
    if (sure) {
        var data = {"res_id": res_id};
        $.ajax({
            url: `/cancel_reservation`,
            method: "POST",
            contentType: "application/json",
            datatype: "json",
            data: JSON.stringify(data),
            success: function () {
                alert("Reservation successfully removed.");
                window.location = "/reservations";
            },
            error: function() {
                alert("error");
            }
        });
        return true;
    } else {
        return false;
    }
}