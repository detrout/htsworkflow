
var getInventoryDataGrid = function(){
    
    var Item = Ext.data.Record.create([
       { name: 'uuid' },
       { name: 'barcode_id'},
       { name: 'model_id'},
       { name: 'part_number'},
       { name: 'lot_number'},
       { name: 'vendor'},
       { name: 'creation_date'/*, type: 'date', dateFormat: 'n/j h:ia'*/},
       { name: 'modified_date'/*, type: 'date', dateFormat: 'n/j h:ia'*/},
       { name: 'location'},
       { name: 'status'},
       { name: 'flowcells'},
       { name: 'type'}
    ]);
    
    var inventoryReader = new Ext.data.JsonReader(
        {
            totalProperty: "results",
            root: "rows",
            idProperty: "uuid"
        },
        Item
    );
    
    /*
    var inventoryStore = new Ext.data.JsonStore({
       autoDestory: true,
       url: '/inventory/data/items/',
       storeId: 'item_store',
       
    });
    */
    
    var grid = new Ext.grid.GridPanel({
        store: new Ext.data.GroupingStore({
            reader: inventoryReader,
            url: '/inventory/data/items/',
            storeId: 'item_group_store',
            groupField: 'type',
            sortInfo: { field: 'creation_date', direction: "DESC"},
            autoLoad: true
        }),
    
        columns: [
            {id: 'uuid', header:"UUID", width: 32, sortable: true, dataIndex: 'uuid'},
            {header: 'Barcode ID', width: 20, sortable: true, dataIndex: 'barcode_id'},
            {header: 'Location', width: 20, sortable: true, dataIndex: 'location'},
            {header: 'Model', width: 20, sortable: true, dataIndex: 'model_id'},
            {header: 'Part #', width: 20, sortable: true, dataIndex: 'part_number', hidden: true},
            {header: 'Lot #', width: 20, sortable: true, dataIndex: 'lot_number', hidden: true},
            {header: 'Vendor', width: 20, sortable: true, dataIndex: 'vendor'},
            {header: 'Creation Date', width: 20, sortable: true, dataIndex: 'creation_date'/*, renderer: Ext.util.Format.dateRenderer('Y/m/d')*/},
            {header: 'Modified Date', width: 20, sortable: true, dataIndex: 'modified_date', hidden: true/*, renderer: Ext.util.Format.dateRenderer('Y/m/d')*/},
            {header: 'Status', width: 20, sortable: true, dataIndex: 'status', hidden: true},
            {header: 'Stored Flowcells', width: 20, sortable: true, dataIndex: 'flowcells'},
            {header: 'Type', width: 20, sortable: true, dataIndex: 'type', hidden: true}
        ],
        
        view: new Ext.grid.GroupingView({
           forceFit: true,
           groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Items" : "Item"]})'
        }),
        
        frame: true,
        width: 'auto',
        //height: 500,
        autoHeight: true,
        collapsible: false,
        title: "Inventory Index",
        iconCls: 'icon-grid',
        id: 'inventory_item_panel',
        stateId: 'inventory_item_panel_state',
        stateful: true,
        //renderTo: 'grid_target'
    });
    
    return grid;
}