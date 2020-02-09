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
    var i;
    for(i = 0; i < images_list.length; i++){
      var image = images_list[i].fields;
      var id = images_list[i].pk;
      addSidebarIcon(sidebar, graph, image, id);
    }
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
    //console.log(string);
    var xml_string = mxUtils.parseXml(string);
    var codec = new mxCodec(xml_string);
    codec.decode(xml_string.documentElement, graph.getModel());
    keyBindings(graph)
    graphListener(graph)
  }
};

function getVector(device)
{
  switch(device.devicetype)
  {
    case "pc":
      return '../static/devices/computer.svg';
    case "switch":
      return '../static/devices/switch.svg';
    case "router":
      return '../static/devices/router.svg';
    case 'server':
      return '../static/devices/server.svg';
    case "mlswitch":
    default:
      return '../static/devices/computer.svg';
  }
}

function graphListener(graph)
{
  // Updates the display
  graph.getModel().addListener('change', function(){
    var encoder = new mxCodec();
    var result = encoder.encode(graph.getModel());
    var xml = mxUtils.getXml(result);
    //console.log('xml', xml);
    //console.log('raw_data', result)
    sendRequest(xml);
  });
}

function addSidebarIcon(sidebar, graph, disk_image, image_id)
{
  var image = getVector(disk_image);
  var funct = function(graph, evt, cell, x, y)
  {
    getDeviceModal(image_id, graph);
    // This function can take the image ID too!!
    var parent = graph.getDefaultParent();
    var model = graph.getModel();
    
    var device = null;
    var stylesheet = `shape=image;image=${image};` +
    `verticalLabelPosition=bottom;verticalAlign=top;`;
    model.beginUpdate();
    try
    {
      device = graph.insertVertex(parent, null, disk_image.name, x, y, 100, 100, stylesheet);
      device.setConnectable(true);
    }
    finally
    {
      model.endUpdate();
    }
    graph.setSelectionCell(device);
  }
  var icon = document.createElement('img');
  icon.setAttribute('src', image);
  icon.setAttribute('data-image-name', disk_image.name)
  icon.setAttribute('data-image-id', image_id)
  icon.setAttribute('id', 'sidebarItem');
  icon.title = 'Drag this onto the canvas to create a new device';
  sidebar.appendChild(icon);

  var description = document.createElement('div');
  description.innerHTML = disk_image.name;
  description.setAttribute('align','center');
  sidebar.appendChild(description); 

  var dragElement = document.createElement('div');
  dragElement.style.border = 'dashed black 1px';
  dragElement.style.width = '150px';
  dragElement.style.height = '150px';

  var ds = mxUtils.makeDraggable(icon,graph,funct,dragElement,0,0,true,true);
  ds.setGuidesEnabled(true);
}

function keyBindings(graph)
{
  var keyHandler = new mxKeyHandler(graph);
  keyHandler.bindKey(46, function(evt)
  {
    if (graph.isEnabled())
    {
      graph.removeCells();
    }
  });
}

function getDeviceModal(image_id, graph)
{
  $('#device_modal').modal('show');
  $('#device_modal').on("hidden.bs.modal", function () {
    if (graph.isEnabled())
    {
      graph.removeCells();
    }
  });
  $('#device_modal').on("shown.bs.modal", function(){
    // do something
  });
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