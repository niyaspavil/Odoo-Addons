/**
 * Created by cybrosys on 7/16/15.
 */
$(document).ready(function() {
                       $('.event_radio_btn').click(function() {
                           if($(this).attr('id') == 'click_me') {
                                $('#show_me').show();
                           }

                           else {
                                $('#show_me').hide();
                           }
                       });
                    });