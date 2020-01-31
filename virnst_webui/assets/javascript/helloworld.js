// Program starts here. Creates a sample graph in the
// DOM node with the specified ID. This function is invoked
// from the onLoad event handler of the document (see below).
function main(container, sidebar)
{
  // Checks if the browser is supported
  if (!mxClient.isBrowserSupported())
  {
    // Displays an error message if the browser is not supported.
    mxUtils.error('Browser is not supported!', 200, false);
  }
  else
  {
    mxConstants.MIN_HOTSPOT_SIZE = 16;
    mxConstants.DEFAULT_HOTSPOT = 1;
    mxGraphHandler.prototype.guidesEnabled = true;

    // Disables the built-in context menu
    mxEvent.disableContextMenu(container);
    
    // Creates the graph inside the given container
    var graph = new mxGraph(container);
    var images_list = getDevices();
    // Enables rubberband selection
    new mxRubberband(graph);
    // Disable highlight of cells when dragging from toolbar
    graph.setDropEnabled(false);

    graph.isCellSelectable = function(cell)
    {
      return !this.isCellLocked(cell);
    };

    // Gets the default parent for inserting new cells. This
    // is normally the first child of the root (ie. layer 0).
    var parent = graph.getDefaultParent();
    var string = getXml();
    console.log(string);
    var xml_string = mxUtils.parseXml(string);
    var codec = new mxCodec(xml_string);
    codec.decode(xml_string.documentElement, graph.getModel());
    
    graphListener(graph)

  }
};

function graphListener(graph)
{
  // Updates the display
  graph.getModel().addListener('change', function(){
    var encoder = new mxCodec();
    var result = encoder.encode(graph.getModel());
    var xml = mxUtils.getXml(result);
    console.log('xml', xml);
    console.log('raw_data', result)
    sendRequest(xml);
  });
}

function addSidebarIcon(sidebar, image, graph)
{
  var funct = function(graph, evt, cell, x, y)
  {
    var parent = graph.getDefaultParent();
    var model = graph.getModel();
    
    var device = null;
    
    model.beginUpdate();
    try
    {
      // code goes here
      device = graph.insertVertex(parent, null, null, x, y, 120, 120);
      device.setConnectable(false);
    }
    finally
    {
      model.endUpdate();
    }
    graph.setSelectionCell(device);
  }
  var icon = document.createElement('img');
  icon.setAttribute('src', image);
  icon.style.width = '120px';
  icon.style.height = '120px';
  icon.title = 'Drag this onto the canvas to create a new device';

  var dragElement = document.createElement('div');
  dragElement.style.width = '150px';
  dragElement.style.height = '150px';

  var ds = mxUtils.makeDraggable(icon,graph,funct,dragElement,0,0,true,true);
  ds.setGuidesEnabled(true);
}

function getDevices()
{
  var output = null;
  $.ajax({
    url: "get_devices",
    async: false,
    success: function(result){
      output = result['disk_images'];
      console.log(output);
    }
  });
  return output;
}

function sendRequest(xml)
{
  $.ajax({
    url: "home",
    data: {'XML': xml},
    success: function(result){
      console.log(result);
    }
  });
}

function getXml()
{
  var output = "";
  $.ajax({
    url: "retrieveXml",
    async: false,
    contentType: "text/xml",
    success: function(result){
      output = result["response"];
    }
  })
  return output;
}
