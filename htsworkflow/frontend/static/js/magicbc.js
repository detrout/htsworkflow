//-----------------------------------------------
// Barcode Magic JavaScript
// Authors: Brandon W. King
// Feb. 2009
//-----------------------------------------------

//---------------------------------------
// BCMagic Core Processing AJAX Callback
//---------------------------------------
var bcmagic_process_callback = function(data, textStatus) {
    if (textStatus != 'success')
    {
        bcmagic_message('AJAX Status: '+textStatus);
        return;
    }
    
    for (key in data)
    {
        if (key == 'mode')
        {
            if (data['mode'] == 'clear')
            {
                bcmagic_status('','');
            }
            else if (data['mode'] == 'redirect')
            {
                if ('url' in data)
                {
                    bcmagic_redirect(data['url']);
                }
                else
                {
                    bcmagic_status('Error', 'No redirect URL provided by server');
                }
            }
            else if (data['mode'] == 'autofill')
            {
                bcmagic_autofill(data['field'], data['value'])
            }
            else {
                bcmagic_message('Message recieved!');
                bcmagic_status(data['mode'], data['status']);    
            }
            
        }
        if (key == 'msg')
        {
            bcmagic_message(data['msg']);
        }
    }
}

var bcmagic_callback = function(data, textStatus)
{
    if (textStatus != 'success')
        bcmagic_message('Failed!');
    else
        bcmagic_message('Success!');
}

var bcmagic_process = function(){
    var magic = $("#id_magic");
    var text = magic.attr('value');
    magic.attr('value', '');
    
    var bcm_mode = $("#id_bcm_mode");
    var mode = bcm_mode.attr('value');
    
    // Show what we have captured
    bcmagic_message('Sent command to server');
    $.post('/bcmagic/magic/', {'text': text, 'bcm_mode': mode}, bcmagic_process_callback, 'json');
}

var bcmagic_keyhandler = function(e) {
    //Process upon enter key as input.
    if (e.which == 13)
      bcmagic_process();
}

//---------------------------------------
// Utility Functions
//---------------------------------------
var bcmagic_message = function(text)
{
    // Show message
    $("#bcm_msg").html(text);
    
    // clear message after 3000ms
    setTimeout(function() {
        $("#bcm_msg").html('');
        }, 3000);
}

var bcmagic_status = function(state, text)
{
    var msg = $('#bcm_status');
    if (state.length > 0 || text.length > 0)
        msg.html('<b>'+state+':</b> '+text);
    else
        msg.html('');
}


var bcmagic_redirect = function(url)
{
    bcmagic_message('Redirecting to:' + url);
    window.location = url;
}

var bcmagic_autofill = function(field, val)
{
    var txtbox = $('#'+field);
    txtbox.attr('value', val);
    
    var input_fields = $('form input').not(':hidden').not('[type=submit]');
    
    // Count the number of text fields which have been filled in.
    var count = 0;
    input_fields.each( function(){
                   if(this.value.length > 0){
                        count = count + 1;
                   }
                });
    
    // If the number of text fields filled in is equal to the number of input_fields in the form, submit the form!
    if (count == input_fields.length)
    {
        bcmagic_status('Form Full', 'Form is now full and ready to process');
        form = $('form');
        form.submit();
        form.reset();
    
    }
    else
    {
        bcmagic_status('Form Fill Count', 'Count(' + count +') - Total(' + input_fields.length + ')');
    }
}

//---------------------------------------
// Main Ready Function
//---------------------------------------
$(document).ready(function() {
        
        // Grab initial focus on magic text input
        $("#id_magic").focus();
        
        // Set some initial text
        //$("#id_magic").attr('value','Moo cow!');
        
        // Trigger when enterkey is pressed
        $("#id_magic").keypress(bcmagic_keyhandler)
});