// fill viewport
var canv = document.getElementById( 'canvas' );
canv.width = window.innerWidth;
canv.height = window.innerHeight;

var cwidth = canv.width;
var cheight = canv.height;
var cdiag = Math.sqrt( cwidth * cwidth + cheight * cheight );

// tunable parameters
var DELAY = 200.0;   // ms
var WIDTH = 2;     // px

var ctx = canv.getContext( '2d' );

ctx.fillStyle = '#000000';
ctx.fillRect( 0, 0, cwidth, cheight );

ctx.globalCompositeOperation = 'xor';
ctx.strokeStyle = '#ffffff';
ctx.lineWidth = WIDTH;
ctx.lineCap = 'round';

function draw()
{
    var x = Math.random() * cwidth;
    var y = Math.random() * cheight;
    var t = Math.random() * 2 * Math.PI;

    ctx.beginPath();

    var dx = cdiag * Math.cos( t );
    var dy = cdiag * Math.sin( t );
    ctx.moveTo( x - dx, y - dy );

    ctx.lineTo( x + dx, y + dy );

    ctx.stroke();
}

window.setInterval( draw, DELAY );
