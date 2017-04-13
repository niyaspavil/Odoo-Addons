$(document).ready(function () {
    $('#myform').each(function () {
        var oe_website_sale = this;
        $( "#datepicker1" ).datepicker({
             changeMonth: true,
             changeYear: true ,
             minDate: 0
        });
        $( "#datepicker2" ).datepicker({
             changeMonth: true,
             changeYear: true ,
             minDate: 0
        });
        $(oe_website_sale).on('click', "button[id='buttApply']", function (event) {
            var from_date =  $("input[id='datepicker1']").val();
            var to_date = $("input[id='datepicker2']").val();
            var accom_type = $("select[name='accom_type']").val();
            if (!from_date) {
                var html1 = '<span style="font-weight: normal; color:RED">Please Choose Date</span>';
                $('#error_from').html(html1);
            }
            if (!to_date) {
                var html2 = '<span style="font-weight: normal; color:RED">Please Choose Date</span>';
                $('#error_to').html(html2);
            }
            if (!accom_type) {
                var html3 = '<span style="font-weight: normal; color:RED">Accommodation can not be empty</span>';
                $('#error_check').html(html3);
            }
            if(from_date && to_date && accom_type) {
                $('#loading').show();
            }
            if (from_date && to_date && accom_type)  {
                openerp.jsonRpc("/accommodation/type", 'call', {
                    from_date: from_date,
                    to_date: to_date,
                    accom_type : accom_type
                })
                .then(function (data) {
                    if (data) {
                       $('#loading').hide();
                       var html = '<thead><tr><th>Date</th><th>Accommodation Type</th><th>Rooms</th><th>Price</th></tr></thead>';

                       for (i in data.date_list) {
                           html += '<tr class="row_select"><td class="type-date"><label style="font-weight: normal"> '+  data.date_list[i] +'</label></td><td>' +
                               '<select class="form-control type-select"><option value="">Choose Type...</option>';
                                for (j in data.categories){
                                    if (data.category_id == data.categories[j][0]) {
                                        html += '<option value="'+ data.categories[j][0] +'" selected>'+ data.categories[j][1] +'</option>';
                                    }
                                    else {
                                        html += '<option value="'+ data.categories[j][0] +'">'+ data.categories[j][1] +'</option>';
                                    }
                                }
                           html += '</select></td>' +
                               '<td><select class="form-control room-select"><option value="">Choose Rooms...</option>';
                           html += '<option value="'+ data.room_id[i][0][0] +'"selected>'+ data.room_id[i][0][1] +'</option>'
                           console.log(data.room_id[i])
                           for (k in data.room_id[i]) {
                               if (k > 0){
                               html += '<option value="'+ data.room_id[i][k][0] +'">'+ data.room_id[i][k][1] +'</option>'
                               }
                           }
                           html+=    '</select></td><td><label style="font-weight: normal"></label>'+data.room_id[i][0][2]+'</td><td></td></tr>';
                       }
                       html += '<tr><td></td><td></td><td></td><td></td><td><button id="btn_click" type="button" class="btn btn-primary btn-lg " style="float: right;">Book Now</button></td></tr>';
                       $('#grid_basic').html(html);
                }});
            }
        });

        $(oe_website_sale).on('change', "select[class='form-control room-select']", function (event) {

            var cur_row = $(this).closest('tr');
            $(cur_row.children('td').eq(3)).html(0.00);
            var room_id = cur_row.children('td').eq(2).find("select").val();
            openerp.jsonRpc("/rooms/cost", 'call', {
                    room_id: room_id
            })
            .then(function (data) {
                var html1 ='<label style="font-weight: normal"> '+  data.list_price +'</label>';
                $(cur_row.children('td').eq(3)).html(html1);
            });
        }).change();

        $(oe_website_sale).on('change', "select[class='form-control type-select']", function (event) {

            var cur_row = $(this).closest('tr');
            var line_date = cur_row.children('td').eq(0).text();
            var accom_id = cur_row.children('td').eq(1).find("select").val();
            openerp.jsonRpc("/rooms/type", 'call', {
                    line_date: line_date,
                    type_id : accom_id
            })
            .then(function (data) {
                var html1 ='<option value="">Choose Rooms...</option>';
                for (i in data.rooms) {
                    html1 += '<option value="'+ data.rooms[i][0] +'"selected>'+ data.rooms[i][1] +'</option>';
                }
                $(cur_row.children('td').eq(2).find("select")).html(html1);
            $(cur_row.children('td').eq(3)).html(data.rooms[0][2]);
                console.log(data.rooms)
            });
        }).change();

        $(oe_website_sale).on('click', "button[id='btn_click']", function (event) {
            var from_date =  $("input[id='datepicker1']").val();
            var to_date = $("input[id='datepicker2']").val();
            var accom_type = $("select[name='accom_type']").val();
            var book_id = $("input[id='book_id']").val();
            var date1 = Array();
            var type1 = Array();
            var room1 = Array();
            var cost1 = Array();
            $("table tr.row_select").each(function(i, v){
                date1[i] = $(this).children('td').eq(0).text();
                type1[i] = $(this).children('td').eq(1).find("select").val();
                room1[i] = $(this).children('td').eq(2).find("select").val();
                cost1[i] = $(this).children('td').eq(3).text();
            });
            openerp.jsonRpc("/accommodation/validate", 'call', {
                book_id: book_id,
                from_date: from_date,
                to_date: to_date,
                accom_type: accom_type,
                data1: date1,
                type1: type1,
                room1: room1,
                cost1: cost1
            })
            .then(function (data) {
                   window.location.href = '/cart/confirmation/'+ data.book_id;
            });
        });
    });
});
