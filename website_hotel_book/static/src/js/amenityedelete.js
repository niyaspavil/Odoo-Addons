$(document).ready(function () {
    $('#aminity_list_form').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('click', "button[class='btn_click']", function (event) {
            event.preventDefault();
            var book_id = $("input[id='book_id']").val();
            var cur_row = $(this).closest('tr');
            var aminity_id = cur_row.children('td').eq(0).find("input").val();
            var curent_id = cur_row.children('td').eq(1).find("input").val();
            openerp.jsonRpc("/aminity/delete", 'call', {
               book_id: book_id,
               aminity_id: aminity_id,
               curent_id: curent_id
            })
            .then(function(data) {
                console.log(data);
                if(data) {
                    $('#loading').hide();
                    location.reload();
                    return;
                }
            });
        });
    });
});