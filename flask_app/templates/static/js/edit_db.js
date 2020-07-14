
function fillSpanComponents(hostname, type, host_comps, comps, comp_ids) {
    var name_aux = hostname + "_" + type;

    if (type == "cpu") {
        host_comps = [host_comps];
    }
    var str_aux = "";
    for (let index = 0; index < host_comps.length; index++) {
        var comp_id = parseInt(host_comps[index]);
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
    document.getElementById(name_aux).innerHTML = str_aux;
    // document.getElementById(name_aux + "_tooltiptext").innerHTML = str_aux;
}

