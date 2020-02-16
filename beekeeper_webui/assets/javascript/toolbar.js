function populateToolbar(graph)
{
  var toolbar = document.getElementById('toolbarContainer');
  addToolbarIcon(toolbar, graph, '../static/devices/ethernet_cable.svg', 'draggable');
}

function addToolbarIcon(toolbar, graph, tool, tooltype)
{
  var funct = function(graph, evt, cell, x, y)
  {
    var parent = graph.getDefaultParent();
    var model = graph.getModel();
    
    var style = `curved=1;endArrow=classic;html=1;`;
    model.beginUpdate();
    try
    {
      var cable = new mxCell('Test Cable', new mxGeometry(0,0,50,50), style);
      cable.geometry.setTerminalPoint(new mxPoint(50,150), true);
      cable.geometry.setTerminalPoint(new mxPoint(150,50), false);

      cell.geometry.relative = true;
      cell.edge = true;

      cell = graph.addCell(cell);
      graph.fireEvent(new mxEventObject('cellsInserted', 'cells', [cell]));
    }
    finally
    {
      model.endUpdate();
    }
    graph.setSelectionCell(cable);
  }

  var icon = document.createElement('img');
  icon.setAttribute('src', tool);
  icon.setAttribute('id', 'toolbarItem');
  icon.title = 'Drag this onto the canvas to create a new ethernet cable';
  toolbar.appendChild(icon);

  var dragElement = document.createElement('div');
  dragElement.style.border = 'dashed black 1px';
  dragElement.style.width = '100px';
  dragElement.style.height = '100px';

  var ds = mxUtils.makeDraggable(icon,graph,funct,dragElement,0,0,true,true);
  ds.setGuidesEnabled(true);
}

function addToolbarButton(toolbar, image, click_function)
{
  var button = document.createElement('button');

  var img = document.createElement('img');
  img.setAttribute('src', image);
  img.style.width = '20px';
  img.style.height = '20px';
  img.style.verticalAlign = 'middle';
  img.style.marginRight = '2px';
  button.appendChild(img);

  // click_function is a custom object passed through as a param in addToolbarButton
  button.addEventListener("click", click_function)
  toolbar.appendChild(button)
}

function startVirtualMachines()
{
  console.log('Starting VMs')
}

function stopVirtualMachines()
{
  console.log('Stopping VMs')
}