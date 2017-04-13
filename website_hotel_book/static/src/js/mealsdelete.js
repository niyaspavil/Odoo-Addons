$(document).ready(function () {
    $('#formmeal').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('click', "button[class='btn btn-primary1']", function (event) {
            event.preventDefault();
            var cur_row = $(this).closest('tr');
            var line_date = cur_row.children('td').eq(0).text();
            var fast_check =cur_row.children('td').eq(1).find("input.fast_select").is(':checked');
            var lnch_check =cur_row.children('td').eq(2).find("input.lunch_select").is(':checked');
            var diner_check =cur_row.children('td').eq(3).find("input.dinner_select").is(':checked');
            var html2 = '<button class="btn btn-primary">Confirm</button>';
            if(fast_check) {
                var html1 = '<input class="fast_select" type="checkbox" checked="checked" />';
                $(cur_row.children('td').eq(1)).html(html1);
            }
            else {
                var html1 = '<input class="fast_select" type="checkbox" />';
                $(cur_row.children('td').eq(1)).html(html1);
            }
            if(lnch_check) {
                var html1 = '<input class="lunch_select" type="checkbox" checked="checked" />';
                $(cur_row.children('td').eq(2)).html(html1);
            }
            else {
                var html1 = '<input class="lunch_select" type="checkbox" />';
                $(cur_row.children('td').eq(2)).html(html1);
            }
            if(diner_check) {
                var html1 = '<input class="dinner_select" type="checkbox" checked="checked" />';
                $(cur_row.children('td').eq(3)).html(html1);
            }
            else {
                var html1 = '<input class="dinner_select" type="checkbox" />';
                $(cur_row.children('td').eq(3)).html(html1);
            }
            $(cur_row.children('td').eq(5)).html(html2);
        });

        $(oe_website_sale).on('click', "button[class='btn btn-primary']", function (event) {
            $('#loading').show();
            event.preventDefault();
            var book_id = $("input[id='book_id']").val();
            var cur_row = $(this).closest('tr');
            var line_date = cur_row.children('td').eq(0).text();
            var cur_id = cur_row.children('td').eq(0).find("input").val();
            var fast_check =cur_row.children('td').eq(1).find("input.fast_select").is(':checked');
            var lnch_check =cur_row.children('td').eq(2).find("input.lunch_select").is(':checked');
            var diner_check =cur_row.children('td').eq(3).find("input.dinner_select").is(':checked');
            openerp.jsonRpc("/meals/edit", 'call', {
                book_id: book_id,
                line_date: line_date,
                cur_id: cur_id,
                fast_check: fast_check,
                lnch_check: lnch_check,
                diner_check: diner_check
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