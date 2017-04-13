$(document).ready(function () {
    var website = openerp.website;
    openerp.jsonRpc("/hotel/timer", 'call')
            .then(function (data) {
            hotel_id = data['hotel_id'];
            time  = data['time'];
            $('#countdown_div').hide();
            if (time != 0){
                $('#countdown_div').show();
                $('#countdown').append('<P>You must Complete Within 30 minute</P>');
                $('#countdown').timer({
	                format: '%M minutes : %s seconds',
	                seconds:time,
                    duration: '30m',
                    callback: function() {
                        alert('Time up!');
                        website.form('/reservation/change', 'POST', {
                        hotel_id: hotel_id

                        });
                    }
            });
                console.log(time);
                if ( time >= (30*60) && hotel_id){
                    alert('Time up!');
                   website.form('/reservation/change', 'POST', {
                    hotel_id: hotel_id
                });
               }
            }
            });

    $('#myform').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('change', "select[name='country_id']", function () {
            var $select = $("select[name='state_id']");
            $select.find("option:not(:first)").hide();
            var nb = $select.find("option[data-country_id="+($(this).val() || 0)+"]").show().size();
            $select.parent().toggle(nb>1);
        }).change();
    });
});
