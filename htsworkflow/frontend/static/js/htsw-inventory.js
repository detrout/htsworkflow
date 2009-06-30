
var getInventoryDataGrid = function(){
    
    var Item = Ext.data.Record.create([
       { name: 'uuid' },
       { name: 'barcode_id'},
       { name: 'creation_date'/*, type: 'date', dateFormat: 'n/j h:ia'*/},
       { name: 'modified_date'/*, type: 'date', dateFormat: 'n/j h:ia'*/},
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
            sortInfo: { field: 'modified_date', direction: "ASC"},
            autoLoad: true
        }),
    
        columns: [
            {id: 'uuid', header:"UUID", width: 32, sortable: true, dataIndex: 'uuid'},
            {header: 'Barcode ID', width: 20, sortable: true, dataIndex: 'barcode_id'},
            {header: 'Creation Date', width: 20, sortable: true, dataIndex: 'creation_date'/*, renderer: Ext.util.Format.dateRenderer('Y/m/d')*/},
            {header: 'Modified Date', width: 20, sortable: true, dataIndex: 'modified_date'/*, renderer: Ext.util.Format.dateRenderer('Y/m/d')*/},
            {header: 'Type', width: 20, sortable: true, dataIndex: 'type'}
        ],
        
        view: new Ext.grid.GroupingView({
           forceFit: true,
           groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Items" : "Item"]})'
        }),
        
        frame: true,
        width: 'auto',
        height: 500,
        //autoHeight: true,
        collapsible: false,
        title: "Inventory Index",
        iconCls: 'icon-grid'
        //renderTo: 'grid_target'
    });
    
    return grid;
}