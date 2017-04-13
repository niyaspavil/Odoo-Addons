$(document).ready(function () {
    $('#myform').each(function () {
        var oe_website_sale = this;
        var rsrv_from =  $("input[id='rsrv_from']").val();
        var rsrv_to = $("input[id='rsrv_to']").val();
        openerp.jsonRpc("/service/type", 'call', {
            rsrv_from: rsrv_from,
            rsrv_to: rsrv_to
        })
        .then(function (data) {
             if (data) {

                       var html = '<thead><tr><th></th><th>Services</th><th>Cost</th></tr></thead>';

                       for (i in data.service_ids) {

                           html+= '<tr class="row_select"><td><input class="service_select" type="checkbox"/></td><td><label style="font-weight: normal"> '+  data.service_ids[i][1] +'</label><input type="hidden" value="' + data.service_ids[i][0] + '" style="width:30%"/></td><td><label style="font-weight: normal"> '+  data.service_ids[i][2] +'</label></td></tr>';
                       }
                       html += '<tr><td></td><td></td><td></td></tr>';

                       html += '<thead><tr><th></th><th>Amenities</th><th>Cost</th></tr></thead>';

                       for (j in data.amenity_ids) {

                           html+= '<tr class="row_deselect"><td><input class="amenity_select" type="checkbox"/></td><td><label style="font-weight: normal"> '+  data.amenity_ids[j][1] +'</label><input type="hidden" value="' + data.amenity_ids[j][0] + '" style="width:30%"/></td><td><label style="font-weight: normal"> '+  data.amenity_ids[j][2] +'</label></td></tr>';
                       }

                       html += '<tr><td></td><td></td><td></td></tr>';
                       html += '<tr><td></td><td></td><td><button id="btn_click1" type="button" class="btn btn-primary btn-lg " style="float: right;">Book Now</button></td></tr>';
                       $('#grid_basic').html(html);
                 }
        });
        $(oe_website_sale).on('click', "button[id='btn_click1']", function (event) {
            event.preventDefault();
            var rsrv_from =  $("input[id='rsrv_from']").val();
            var rsrv_to = $("input[id='rsrv_to']").val();
            var book_id = $("input[id='book_id']").val();
            var service = Array();
            var amenity = Array();
            var scost = Array();
            var acost = Array();
            $("table tr.row_select").each(function(i, v){
                var srvc_box  = $(this).children('td').eq(0).find("input.service_select").is(':checked');
                 if (srvc_box) {
                    service[i] = $(this).children('td').eq(1).find("input").val();
                    scost[i] = $(this).children('td').eq(2).text();
                }
            });
            $("table tr.row_deselect").each(function(i, v){
                var check_box  = $(this).children('td').eq(0).find("input.amenity_select").is(':checked');
                if (check_box) {
                    amenity[i] = $(this).children('td').eq(1).find("input").val();
                    acost[i] = $(this).children('td').eq(2).text();
                }
            });
            openerp.jsonRpc("/service/validate", 'call', {
                book_id: book_id,
                rsrv_from: rsrv_from,
                rsrv_to: rsrv_to,
                service: service,
                scost: scost,
                amenity: amenity,
                acost: acost
            })
            .then(function (data) {
                   window.location.href = '/cart/confirmation/' + data.book_id;
            });
        });
    });
});