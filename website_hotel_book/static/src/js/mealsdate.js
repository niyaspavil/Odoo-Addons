$(document).ready(function () {
    $('#myform').each(function () {
        var oe_website_sale = this;
        var rsrv_from =  $("input[id='rsrv_from']").val();
        var rsrv_to = $("input[id='rsrv_to']").val();
        openerp.jsonRpc("/meals/type", 'call', {
            rsrv_from: rsrv_from,
            rsrv_to: rsrv_to
        })
        .then(function (data) {
             if (data) {
                 $('#loading').hide();
                 var html = '<thead><tr><th>Date</th><th><input class="brk_all" type="checkbox" />Breakfast</th><th><input class="lunch_all" type="checkbox" />Lunch</th><th><input class="dinner_all" type="checkbox" />Dinner</th></tr></thead>';
                 for (i in data.date_list) {
                     html += '<tr class="row_select"><td class="type-date"><label style="font-weight: normal"> '+  data.date_list[i] +'</label></td><td>' +
                     '<input class="fast_select" type="checkbox" /></td><td><input class="lunch_select" type="checkbox"/></td><td><input class="dinner_select" type="checkbox"/></td>';

                 }
                 html += '<tr><td></td><td></td><td></td><td><button id="btn_click" type="button" class="btn btn-primary btn-lg " style="float: right;">Book Now</button></td></tr>';
                 $('#grid_basic').html(html);
            }
        });

        $(oe_website_sale).on('click', "input[class='brk_all']", function(event) {
            if ($('.brk_all').attr('checked')) {
                $("table tr.row_select").each(function(i, v){
                    $('.fast_select').attr({'checked': true});
                });
            } else {
                $("table tr.row_select").each(function(i, v){
                    $('.fast_select').attr({'checked': false});
                });
            }
        });

        $(oe_website_sale).on('click', "input[class='lunch_all']", function(event) {
            if ($('.lunch_all').attr('checked')) {
                $("table tr.row_select").each(function(i, v){
                    $('.lunch_select').attr({'checked': true});
                });
            } else {
                $("table tr.row_select").each(function(i, v){
                    $('.lunch_select').attr({'checked': false});
                });
            }
        });

        $(oe_website_sale).on('click', "input[class='dinner_all']", function(event) {
            if ($('.dinner_all').attr('checked')) {
                $("table tr.row_select").each(function(i, v){
                    $('.dinner_select').attr({'checked': true});
                });
            }else {
                $("table tr.row_select").each(function(i, v){
                    $('.lunch_select').attr({'checked': false});
                });
            }
        });

        $(oe_website_sale).on('click', "button[id='btn_click']", function (event) {
            var rsrv_from =  $("input[id='rsrv_from']").val();
            var rsrv_to = $("input[id='rsrv_to']").val();
            var book_id = $("input[id='book_id']").val();
            var date1 = Array();
            var fast1 = Array();
            var lunch1 = Array();
            var dinner1 = Array();
            $("table tr.row_select").each(function(i, v){
                date1[i] = $(this).children('td').eq(0).text();
                fast1[i] = $(this).children('td').eq(1).find("input.fast_select").is(':checked');
                lunch1[i] = $(this).children('td').eq(2).find("input.lunch_select").is(':checked');
                dinner1[i] = $(this).children('td').eq(3).find("input.dinner_select").is(':checked');
            });
            openerp.jsonRpc("/meals/validate", 'call', {
                book_id: book_id,
                rsrv_from: rsrv_from,
                rsrv_to: rsrv_to,
                data1: date1,
                fast1: fast1,
                lunch1: lunch1,
                dinner1: dinner1
            })
            .then(function (data) {
                   window.location.href = '/cart/confirmation/'+ data.book_id;
            });
        });
    });
});