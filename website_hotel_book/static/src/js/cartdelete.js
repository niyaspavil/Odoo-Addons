$(document).ready(function () {
    $('#event_list_form').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('click', "button[class='btn_click']", function (event) {
            event.preventDefault();
            var book_id = $("input[id='book_id']").val();
            var cur_row = $(this).closest('tr');
            var event_id = cur_row.children('td').eq(0).find("input").val();
            var ticket_id = cur_row.children('td').eq(1).find("input").val();

            openerp.jsonRpc("/hotel/delete", 'call', {
               book_id: book_id,
               event_id: event_id,
               ticket_id: ticket_id
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

    $('#formroom').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('click', "button[class='btn_click']", function (event) {
            event.preventDefault();
            var book_id = $("input[id='book_id']").val();
            var cur_row = $(this).closest('tr');
            var accomdtion_id = cur_row.children('td').eq(0).find("input").val();
            var ticket_id = cur_row.children('td').eq(1).find("input").val();

            openerp.jsonRpc("/hotel/delete", 'call', {
               book_id: book_id,
               event_id: event_id,
               ticket_id: ticket_id
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

