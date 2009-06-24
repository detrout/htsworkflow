Ext.state.Manager.setProvider(new Ext.state.CookieProvider());

Ext.override(Ext.Panel,{
  getState: function() {
    return { collapsed: this.collapsed };
    }
});

var quick_msg = function(msg)
{
    Ext.MessageBox.show({
        title: 'Info',
        msg: msg,
        buttons: Ext.MessageBox.OK,
        icon: Ext.MessageBox.INFO
    });
}

var goto_url = function(www_url)
{
    window.location = www_url; 
}

$(document).ready(function(){
    
    //----------------------------------------
    // Dynamically Generate Panels from HTML!
    var create_dynamic_panels = function(){
        var wp_items = Ext.fly('west_panel_items');
        var ul_items = wp_items.query('ul');
        
        var dynamic_panels = new Array();
        Ext.each(ul_items, function(ul) {
            var panel_obj = new Ext.Panel({
                frame: true,
                title: ul.id,
                //collapsible: true,
                //titleCollapse: true,
                //collapsed: true,
                //stateful: true,
                //stateId: 'freezer_panel_state',
		margins: '0 0 0 0',
		//width: 200,
                contentEl: ul
                //stateEvents: ['collapse', 'expand']
            });
            dynamic_panels.push(panel_obj);
        });
        return dynamic_panels;
    }
    
    var panel_bcmagic = new Ext.Panel({
        //title: 'BC Magic',
        unstyled: true,
        contentEl: 'bcmagic_div',
        height: 180
    });
    
    var menuPanel = new Ext.Panel({
        id: 'menu_panel',
        region: 'west',
        collapsible: true,
	split: true,
        margins: '4 0 0 0',
        //cmargins: '2 2 0 2',
        collapseMode: 'mini',
        width: 200,
        minWidth: 150,
        border: false,
        //baseCls: 'x-plain',
        unstyled: true,
        layout: 'vbox',
        layoutConfig: {
            align: 'stretch',
            pack: 'start'
        },
        // Add dynamically generated panels from html and include barcode magic
       items: create_dynamic_panels().concat([panel_bcmagic])
    });
    
    //-------------------------------
    // Main Viewport Setup
    //-------------------------------
    var mainBorderPanel = new Ext.Viewport({
       layout: 'border',
       items: [{
            region: 'north',
            layout: 'vBox',
            layoutConfig: {
                align: 'stretch',
                pack: 'start'
            },
            items: [{
                    xtype: 'box',
                    applyTo: 'header',
                    id: 'header-panel',
                    height: 30
                },{
                    id: 'main_toolbar',
                    xtype: 'toolbar',
                    //height: 100,
                    /*items: [{
                        text: "Demo Button",
                        handler: function() { quick_msg('Messages can be fun!'); }
                    }],*/
                    margins: '2 0 0 0'
            }],
            height: 60 
       },menuPanel,{
            //title: 'Body',
            region: 'center',
            xtype: 'panel',
	    //autoScroll: true,
            layout: 'fit',
            margins: '2 2 2 2',
            items: {
                //title: 'Inner Panel',
                contentEl: 'body_content',
                border: true,
		autoScroll: true
            }
       }]
    });
    
    //-------------------------------
    // Menu Bar Setup
    //-------------------------------
    var main_tb = Ext.getCmp('main_toolbar');
    
    var add_buttons_from_html_left = function(main_tb){
        var left_tbar_data = Ext.fly('left_tbar_data');
        var div_array = left_tbar_data.query('div');
        var div_id = null;
        // Loop through each div since it defines a button and link or a spacer and add it to the right side of the toolbar
        Ext.each(div_array, function(divobj) {
            div_id = divobj.id;
            if (div_id == 'spacer'){
                main_tb.add('-');
            } else {
                main_tb.add({
                    text: div_id,
                    handler: function() { goto_url(divobj.getAttribute('href')); }
                });
            }
        });
        //return right_tbar_data;
    }
    
    var add_buttons_from_html_right = function(main_tb){
        var right_tbar_data = Ext.fly('right_tbar_data');
        var div_array = right_tbar_data.query('div');
        var div_id = null;
        // Loop through each div since it defines a button and link or a spacer and add it to the right side of the toolbar
        Ext.each(div_array, function(divobj) {
            div_id = divobj.id;
            if (div_id == 'spacer'){
                main_tb.add('-');
            } else {
                main_tb.add({
                    text: div_id,
                    handler: function() { goto_url(divobj.getAttribute('href')); }
                });
            }
        });
        //return right_tbar_data;
    }
    
    add_buttons_from_html_left(main_tb);
    
    // Shifts the remaining toolbar options to the right side.
    main_tb.add({ xtype: 'tbfill' });
    var user_info = Ext.fly('login_info');
    var logout_url = user_info.getAttribute('logouturl');
    var login_url = user_info.getAttribute('loginurl');
    
    if (user_info.getAttribute('authenticated') == 'true') {
        main_tb.add({
                        xtype: 'tbtext',
                        text: 'User: ' + user_info.getAttribute('user')
                    });
        main_tb.add('-');
        add_buttons_from_html_right(main_tb);
        main_tb.add('-');
	main_tb.add({
                        text: 'Logout',
                        handler: function() { goto_url(logout_url); }
                    });
        
    } else {
        main_tb.add({
                        text: 'Login',
                        handler: function() { goto_url(login_url) }
                    });
    }
    
    main_tb.doLayout();
    
});