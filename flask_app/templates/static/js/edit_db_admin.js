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
            window.location = "/edit_hosts";
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

// Allows users to edit the setup of a host
function editHost(btn) {
    hostname = btn.value;
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


        // saves previous values
        editdb_old_ip = ip.innerText;
        editdb_old_cpu = getValues(hostname + "_cpu");
        editdb_old_gpu = getValues(hostname + "_gpu");
        editdb_old_fpga = getValues(hostname + "_fpga");

        console.log(editdb_old_ip);
        console.log(editdb_old_cpu);
        console.log(editdb_old_gpu);
        console.log(editdb_old_fpga);

        // swaps the ip field with an input field
        var input = document.createElement('input');
        input.type = 'text';
        input.id = "myInputip";
        input.value = ip.innerHTML;
        ip.innerHTML = '';
        ip.appendChild(input);

        // enables the SELECTs
        editdb_list_selects_cpu[hostname].enable();
        editdb_list_selects_gpu[hostname].enable();
        editdb_list_selects_fpga[hostname].enable();

        return true;
    } else {
        if (hostname == editdb_edit_host) {
            // confirm was pressed
            var ip_input = document.getElementById("myInputip");

            var selected_ip = ip_input.value;
            var selected_cpu = getValues(hostname + "_cpu");
            var selected_gpu = getValues(hostname + "_gpu");
            var selected_fpga = getValues(hostname + "_fpga");

            console.log(editdb_old_ip);
            console.log(selected_ip);
            console.log(selected_cpu);
            console.log(editdb_old_cpu);
            console.log(selected_gpu);
            console.log(editdb_old_gpu);
            console.log(selected_fpga);
            console.log(editdb_old_fpga);

            // Check if there was any change made
            if (selected_ip != editdb_old_ip || selected_cpu != editdb_old_cpu || selected_gpu != editdb_old_gpu || selected_fpga != editdb_old_fpga) {
                // Changes were made, need to be updated in the DB
                var data = { "hostname": hostname, "ip": selected_ip, "cpu": selected_cpu, "gpu": selected_gpu, "fpga": selected_fpga};
                $.ajax({
                    url: "/update_host",
                    method: "POST",
                    contentType: "application/json",
                    datatype: "json",
                    data: JSON.stringify(data),
                    success: function () {
                        window.location = "/edit_hosts";
                    },
                    error: function () {
                        alert("error");
                    }
                });
                return true;
            } else {
                // No changes were made
                var ip = document.getElementsByName(hostname + "_" + editdb_idx_ip)[0];
                var cpu = document.getElementsByName(hostname + "_" + editdb_idx_cpu)[0];
                var gpu = document.getElementsByName(hostname + "_" + editdb_idx_gpu)[0];
                var fpga = document.getElementsByName(hostname + "_" + editdb_idx_fpga)[0];
                ip.innerHTML = editdb_old_ip;
                cpu.innerHTML = editdb_old_cpu;
                gpu.innerHTML = editdb_old_gpu;
                fpga.innerHTML = editdb_old_fpga;
                
                // Reset button style
                btn.style.background = "#586e75";
                btn.innerHTML = "Edit";
                
                // Reset global variables
                editdb_edit = false;
                editdb_edit_host = "";
                editdb_old_ip = "";
                editdb_old_cpu = "";
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
            var cpu = getValues("cpu");
            console.log(cpu);
            if (cpu == "") {
                alert("Please select one CPU from the list.");
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


function removeComponent(comp_id) {
    var sure = window.confirm("Are you sure you want to remove this Component?\n\nWarning: This will remove the component from any corresponding host.");
    if (sure) {
        var data = { "comp_id": comp_id };
        return $.ajax({
            url: "/remove_component",
            method: "POST",
            contentType: "application/json",
            datatype: "json",
            data: JSON.stringify(data),
            success: function () {
                window.location = "/edit_components";
            },
            error: function () {
                alert("error");
            }
        });
    } else {
        return false;
    }
}

// Allows users to edit the characteristics of a component
function editComponent(btn) {
    comp_id = btn.value;
    // Checks if there was already a host being edited (only allowed 1 at a time)
    if (!(editcomp_edit)) {

        // some global variables
        editcomp_edit = true;
        editcomp_edit_comp = comp_id;

        // change button
        btn.style.background = "#268bd2";
        btn.innerHTML = "Confirm";

        // fields that can be edited
        var name = document.getElementsByName(comp_id + "_" + 2)[0];
        var gen = document.getElementsByName(comp_id + "_" + 3)[0];
        var brand = document.getElementsByName(comp_id + "_" + 4)[0];

        // saves previous values
        editcomp_old_name = name.innerText;
        editcomp_old_brand = brand.innerText;
        editcomp_old_gen = gen.innerText;

        // swaps the ip field with an input field
        var input_name = document.createElement('input');
        input_name.type = 'text';
        input_name.id = "myInput-name";
        input_name.value = name.innerHTML;
        name.innerHTML = '';
        name.appendChild(input_name);

        var input_gen = document.createElement('input');
        input_gen.type = 'text';
        input_gen.id = "myInput-gen";
        input_gen.value = gen.innerHTML;
        gen.innerHTML = '';
        gen.appendChild(input_gen);

        var input_brand = document.createElement('input');
        input_brand.type = 'text';
        input_brand.id = "myInput-brand";
        input_brand.value = brand.innerHTML;
        brand.innerHTML = '';
        brand.appendChild(input_brand);

        return true;
    } else {
        if (comp_id == editcomp_edit_comp) {
            // confirm was pressed
            var name_input = document.getElementById("myInput-name");
            var gen_input = document.getElementById("myInput-gen");
            var brand_input = document.getElementById("myInput-brand");
            var selected_name = name_input.value;
            var selected_gen = gen_input.value;
            var selected_brand = brand_input.value;

            console.log(selected_name);
            console.log(editcomp_old_name);
            console.log(selected_gen);
            console.log(editcomp_old_gen);
            console.log(selected_brand);
            console.log(editcomp_old_brand);

            // Check if there was any change made
            if (selected_name != editcomp_old_name || selected_brand != editcomp_old_brand || selected_gen != editcomp_old_gen) {
                // Changes were made, need to be updated in the DB
                var data = { "id": comp_id, "name": selected_name, "brand": selected_brand, "gen": selected_gen};
                $.ajax({
                    url: "/update_component",
                    method: "POST",
                    contentType: "application/json",
                    datatype: "json",
                    data: JSON.stringify(data),
                    success: function () {
                        window.location = "/edit_components";
                    },
                    error: function () {
                        alert("error");
                    }
                });
                return true;
            } else {
                // No changes were made
                var name = document.getElementsByName(comp_id + "_" + 2)[0];
                var gen = document.getElementsByName(comp_id + "_" + 3)[0];
                var brand = document.getElementsByName(comp_id + "_" + 4)[0];

                name.innerHTML = editcomp_old_name;
                gen.innerHTML = editcomp_old_gen;
                brand.innerHTML = editcomp_old_brand;

                // Reset button style
                btn.style.background = "#586e75";
                btn.innerHTML = "Edit";

                // Reset global variables
                editcomp_edit = false;
                editcomp_edit_comp = "";
                editcomp_old_name = "";
                editcomp_old_brand = "";
                editcomp_old_gen = "";
                return true;
            }
        } else {
            return false;
        }
    }
}

function verifyNewComponent() {
    // Checks if all fields were completed
    var type = getValues("comptype");
    console.log(type);
    if (type == "") {
        alert("Please select the Component type from the list.");
        return false;
    } else {
        var compname = document.forms["new_comp_form"]["compname"].value;
        if (compname == "") {
            alert("Component name must be filled out.");
            return false;
        } else {
            var compbrand = document.forms["new_comp_form"]["compbrand"].value;
            if (compbrand == "") {
                alert("Component brand must be filled out.");
                return false;
            } else {
                return true;
            }
        }
    }
}

function createCustomSelects(hostname, type, items, comps, comp_ids, global_list) {
    var name_aux = hostname + "_" + type;

    // add custom multiselect
    if (type == "cpu") {
        var select_aux = new vanillaSelectBox("#" + name_aux, {
            "maxHeight": 200
        });
    } else {
        var select_aux = new vanillaSelectBox("#" + name_aux, {
            "maxHeight": 200,
            "placeHolder": "-- None --",
            translations: { "items": items }
        });
    }

    // make the select boxes smaller only here 
    var special_div = document.getElementById("btn-group-" + "#" + name_aux);
    special_div.classList.add("smaller");

    // disable the select box
    select_aux.disable();

    // add to global list of selects
    global_list[hostname] = select_aux;

    addToolip(name_aux, comp_ids, comps);
}

function addToolip(name_aux, comp_ids, comps) {
    // add tooltip with the current components
    var sel_comps = getValues(name_aux);
    var str_aux = "";
    for (let index = 0; index < sel_comps.length; index++) {
        var comp_id = parseInt(sel_comps[index]);
        for (let index_2 = 0; index_2 < comp_ids.length; index_2++) {
            var id_aux = comp_ids[index_2];
            if (id_aux == comp_id) {
                if (str_aux != "") {
                    str_aux += "; ";
                }
                str_aux += comps[index_2];
            }
        }
    }
    if (str_aux == "") {
        str_aux = "None";
    }
    document.getElementById(name_aux + "_tooltiptext").innerHTML = str_aux;
}

// Allows users to edit the characteristics of a component
function editResType(btn) {
    res_id = btn.value;

    // Checks if there was already a host being edited (only allowed 1 at a time)
    if (!(editrestype_edit)) {

        // some global variables
        editrestype_edit = true;
        editrestype_typeid = res_id;

        // change button
        btn.style.background = "#268bd2";
        btn.innerHTML = "Confirm";

        // fields that can be edited
        var name = document.getElementsByName(res_id + "_name")[0];
        var description = document.getElementsByName(res_id + "_description")[0];

        // saves previous values
        editrestype_old_name = name.innerText;
        editrestype_old_description = description.innerText;

        // swaps the ip field with an input field
        var input_name = document.createElement('input');
        input_name.type = 'text';
        input_name.id = "myInput-name";
        input_name.value = name.innerHTML;
        name.innerHTML = '';
        name.appendChild(input_name);

        var input_description = document.createElement('input');
        input_description.type = 'text';
        input_description.id = "myInput-description";
        input_description.value = description.innerHTML;
        description.innerHTML = '';
        description.appendChild(input_description);

        return true;
    } else {
        if (res_id == editrestype_typeid) {
            // confirm was pressed
            var name_input = document.getElementById("myInput-name");
            var description_input = document.getElementById("myInput-description");
            var selected_name = name_input.value;
            var selected_description = description_input.value;

            console.log(selected_name);
            console.log(editrestype_old_name);
            console.log(selected_description);
            console.log(editrestype_old_description);

            // Check if there was any change made
            if (selected_name != editrestype_old_name || selected_description != editrestype_old_description) {
                // Changes were made, need to be updated in the DB
                var data = { "id": res_id, "name": selected_name, "description": selected_description };
                $.ajax({
                    url: "/update_reservation_type",
                    method: "POST",
                    contentType: "application/json",
                    datatype: "json",
                    data: JSON.stringify(data),
                    success: function () {
                        window.location = "/reservations";
                    },
                    error: function () {
                        alert("error");
                    }
                });
                return true;
            } else {
                // No changes were made
                var name = document.getElementsByName(res_id + "_name")[0];
                var description = document.getElementsByName(res_id + "_description")[0];

                name.innerHTML = editrestype_old_name;
                description.innerHTML = editrestype_old_description;

                // Reset button style
                btn.style.background = "#586e75";
                btn.innerHTML = "Edit";

                // Reset global variables
                editrestype_edit = false;
                editrestype_typeid = "";
                editrestype_old_name = "";
                editrestype_old_description = "";
                return true;
            }
        } else {
            return false;
        }
    }
}

function removeResType(res_id) {
    var sure = window.confirm("Are you sure you want to remove this Reservation Type?");
    if (sure) {
        var data = { "res_id": res_id };
        return $.ajax({
            url: "/remove_reservation_type",
            method: "POST",
            contentType: "application/json",
            datatype: "json",
            data: JSON.stringify(data),
            success: function () {
                window.location = "/reservations";
            },
            error: function () {
                alert("error");
            }
        });
    } else {
        return false;
    }
}