function send_ajax_host(hostname, page) {
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
}


function toggleEnableHost(hostname) {
    return send_ajax_host(hostname, `/toggle_host`);
}

function removeHost(hostname) {
    var sure = window.confirm("Are you sure you want to remove this host?\n\nWarning: This will remove all reservations associated with this host.");
    if (sure) {
        return send_ajax_host(hostname, `/remove_host`);
    } else {
        return false;
    }
}

function addSelectList(field, name, def_value) {
    var selectList = document.createElement("select");
    console.log(selectList);
    selectList.id = "mySelect"+name;
    field.innerHTML = "";
    field.appendChild(selectList);

    options = ["Yes", "No"];
    for (let index = 0; index < 2; index++) {
        var option = document.createElement("option");
        option.value = options[index];
        option.text = options[index];
        selectList.appendChild(option);
    }
    selectList.value = def_value;

    // selectList.style.padding = "0 0";
    // selectList.style.margin = "0 0";
    // selectList.style.width = "auto";
}

// Allows users to edit the setup of a host
function editHost(btn) {
    var hostname = btn.value;

    // Checks if there was already a host being edited (only allowed 1 at a time)
    if (!(editdb_edit)) {

        // some global variables
        editdb_edit = true;
        editdb_edit_host = hostname;

        // change button
        btn.style.background = "#268bd2";
        btn.innerHTML = "Confirm";

        // fields that can be edited
        var ip = document.getElementsByName(hostname + "_" + editdb_idx_ip)[0];
        var gpu = document.getElementsByName(hostname + "_" + editdb_idx_gpu)[0];
        var fpga = document.getElementsByName(hostname + "_" + editdb_idx_fpga)[0];

        // saves previous values
        editdb_old_ip = ip.innerText;
        editdb_old_gpu = gpu.innerText;
        editdb_old_fpga = fpga.innerText;

        // swaps the ip field with an input field
        var input = document.createElement('input');
        input.type = 'text';
        input.id = "myInputip";
        input.value = ip.innerHTML;
        ip.innerHTML = '';
        ip.appendChild(input);

        // swaps the gpu and fpga fields with select fields
        addSelectList(gpu, "gpu", editdb_old_gpu);
        addSelectList(fpga, "fpga", editdb_old_fpga);

        return true;
    } else {
        if (hostname == editdb_edit_host) {
            // confirm was pressed
            var ip_input = document.getElementById("myInputip");
            var gpu_select = document.getElementById("mySelectgpu");
            var fpga_select = document.getElementById("mySelectfpga");
            var selected_ip = ip_input.value;
            var selected_gpu = gpu_select.options[gpu_select.selectedIndex].text;
            var selected_fpga = fpga_select.options[fpga_select.selectedIndex].text;

            console.log(selected_ip);
            console.log(selected_gpu);
            console.log(selected_fpga);

            // Check if there was any change made
            if (selected_ip != editdb_old_ip || selected_gpu != editdb_old_gpu || selected_fpga != editdb_old_fpga) {
                // Changes were made, need to be updated in the DB
                var data = { "hostname": hostname, "ip": selected_ip, "gpu": selected_gpu, "fpga": selected_fpga};
                $.ajax({
                    url: "/update_host",
                    method: "POST",
                    contentType: "application/json",
                    datatype: "json",
                    data: JSON.stringify(data),
                    success: function () {
                        window.location = "/edit";
                    },
                    error: function () {
                        alert("error");
                    }
                });
                return true;
            } else {
                // No changes were made
                var ip = document.getElementsByName(hostname + "_" + editdb_idx_ip)[0];
                var gpu = document.getElementsByName(hostname + "_" + editdb_idx_gpu)[0];
                var fpga = document.getElementsByName(hostname + "_" + editdb_idx_fpga)[0];
                ip.innerHTML = editdb_old_ip;
                gpu.innerHTML = editdb_old_gpu;
                fpga.innerHTML = editdb_old_fpga;
                
                // Reset button style
                btn.style.background = "#586e75";
                btn.innerHTML = "Edit";
                
                // Reset global variables
                editdb_edit = false;
                editdb_edit_host = "";
                editdb_old_ip = "";
                editdb_old_gpu = "";
                editdb_old_fpga = "";
                return true;
            }
        } else {
            return false;
        }
    }
}

function verifyNewHost() {
    // Checks if all fields were completed
    var host = document.forms["new_host_form"]["hostname"].value;
    if (host == "") {
        alert("Hostname must be filled out.");
        return false;
    } else {
        var ipaddr = document.forms["new_host_form"]["ipaddr"].value;
        if (ipaddr == "") {
            alert("IP address must be filled out.");
            return false;
        } else {

            var hasgpu = document.forms["new_host_form"]["hasgpu"].value;
            if (hasgpu === "") {
                alert("Please confirm if host has GPU.");
                return false;
            } else {
                var hasfpga = document.forms["new_host_form"]["hasfpga"].value;
                if (hasfpga === "") {
                    alert("Please confirm if host has FPGA.");
                    return false;
                } else {
                    // Confirm if IP address is a valid Integer
                    if (isNaN(ipaddr)) {          
                        alert("IP address must be an integer.");
                        return false;
                    } else {
                        if (+ipaddr < 256 && +ipaddr>=0) {
                            return true;
                        } else {
                            alert("Invalid IP address.");
                            return false;
                        }
                    }
                }
            }
        }
    }
}