$(document).ready(function () {
    $('#service_list_form').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('click', "button[class='btn_click']", function (event) {
            event.preventDefault();
            var book_id = $("input[id='book_id']").val();
            var cur_row = $(this).closest('tr');
            var srvs_id = cur_row.children('td').eq(0).find("input").val();
            var curent_id = cur_row.children('td').eq(1).find("input").val();
            openerp.jsonRpc("/service/delete", 'call', {
               book_id: book_id,
               srvs_id: srvs_id,
               curent_id: curent_id
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