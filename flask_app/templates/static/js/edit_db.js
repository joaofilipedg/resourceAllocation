function send_ajax_host(hostname, page) {
    var sure = window.confirm("Are you sure you want to remove this host?");
    if (sure) {
            var data = { "hostname": hostname };
        $.ajax({
            url: page,
            method: "POST",
            contentType: "application/json",
            datatype: "json",
            data: JSON.stringify(data),
            success: function () {
                // alert("Reservation successfully removed.");
                window.location = "/edit";
            },
            error: function () {
                alert("error");
            }
        });
        return true;
    } else {
        return false;
    }
}


function toggleEnableHost(hostname) {
    return send_ajax_host(hostname, `/toggle_host`);
}

function removeHost(hostname) {
    return send_ajax_host(hostname, `/remove_host`);
}