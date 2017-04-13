$(document).ready(function () {
    $('#cancel_cart_form').each(function () {
        var oe_website_sale = this;
        $('input[type="radio"]').click(function() {
            if($(this).attr('id') == 'click_me') {
                $('#show_me').show();
                $('#show_mels').hide();
                $('#show_my').hide();
                $('#show_srvc').hide();
            }

            if ($(this).attr('id') == 'click_mels'){
                $('#show_my').hide();
                $('#show_me').hide();
                $('#show_mels').show();
                $('#show_srvc').hide();
            }
            if ($(this).attr('id') == 'click_my') {
                $('#show_my').show();
                $('#show_me').hide();
                $('#show_mels').hide();
                $('#show_srvc').hide();
            }
            if ($(this).attr('id') == 'click_srvc') {
                $('#show_my').hide();
                $('#show_me').hide();
                $('#show_mels').hide();
                $('#show_srvc').show();
            }
        });
    });
});