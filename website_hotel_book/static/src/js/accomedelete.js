$(document).ready(function () {


    $('#formroom').each(function () {
        var oe_website_sale = this;
        var old_roomid=false;
        $(oe_website_sale).on('click', "button[class='btn btn-primary1']", function (event) {
            event.preventDefault();
            var cur_row = $(this).closest('tr');
            var line_date = cur_row.children('td').eq(0).text();
            var accom_id = cur_row.children('td').eq(1).find("select").val();
            old_roomid = cur_row.children('td').eq(2).find("input").val();
            openerp.jsonRpc("/room/change", 'call', {
                line_date: line_date,
                accom_id: accom_id
            })
            .then(function (data) {
                var html1 ='<select class="form-control room-select"><option value="">Cancel Reservation...</option>';
                for (i in data.rooms) {
                    html1 += '<option value="'+ data.rooms[i][0] +'">'+ data.rooms[i][1] +'</option>';
                }
                html1 +=    '</select>';
                var html2 = '<button class="btn btn-primary">Confirm</button>';
                $(cur_row.children('td').eq(2).find("h4")).html(html1);
                $(cur_row.children('td').eq(5)).html(html2);

            });
        });

        $(oe_website_sale).on('change', "select[class='form-control room-select']", function (event) {
            event.preventDefault();
            var cur_row = $(this).closest('tr');
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
            event.preventDefault();
            var cur_row = $(this).closest('tr');
            $(cur_row.children('td').eq(3)).html('');
            var line_date = cur_row.children('td').eq(0).text();
            var accom_id = cur_row.children('td').eq(1).find("select").val();
            openerp.jsonRpc("/rooms/type", 'call', {
                    line_date: line_date,
                    type_id : accom_id
            })
            .then(function (data) {
                var html1 ='<option value="">Cancel Reservation...</option>';
                for (i in data.rooms) {
                    html1 += '<option value="'+ data.rooms[i][0] +'">'+ data.rooms[i][1] +'</option>';
                }
                $(cur_row.children('td').eq(2).find("select")).html(html1);
            });
        }).change();

        $(oe_website_sale).on('click', "button[class='btn btn-primary']", function (event) {
            $('#loading').show();
            event.preventDefault();
            var book_id = $("input[id='book_id']").val();
            var cur_row = $(this).closest('tr');
            var line_date = cur_row.children('td').eq(0).text();
            var cur_id = cur_row.children('td').eq(0).find("input").val();
            var accom_id = cur_row.children('td').eq(1).find("select").val();
            var room_id = cur_row.children('td').eq(2).find("select").val();
            var cost = cur_row.children('td').eq(3).text();
                openerp.jsonRpc("/room/edit", 'call', {
                    book_id: book_id,
                    old_roomid: old_roomid,
                    line_date: line_date,
                    cur_id: cur_id,
                    accom_id: accom_id,
                    room_id: room_id,
                    cost: cost
                })
                .then(function(data) {
                    if(data) {
                        $('#loading').hide();
                        location.reload();
                        return;
                    }
                });
        });
    });
});