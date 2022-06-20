// fill viewport
var canv = document.getElementById( 'canvas' );
canv.width = window.innerWidth;
canv.height = window.innerHeight;

var cwidth = canv.width;
var cheight = canv.height;
var x = cwidth / 2.0;
var y = cheight / 2.0;
var t = 0.0;

var img = document.getElementById( 'image' );
var iwidth = img.clientWidth;
var iheight = img.clientHeight;


// tunable parameters
var STEP = 5.0;     // px
var CURVE = 0.6;    // rad
var DELAY = 20.0;   // ms
var WIDTH = 15;     // px
var ALPHA = 0.3;      // 0..1

var ctx = canv.getContext( '2d' );

ctx.fillStyle = 'rgba( 200, 200, 200, 1 )';
ctx.fillRect( 0, 0, cwidth, cheight );

ctx.globalCompositeOperation = 'destination-out';
ctx.strokeStyle = 'rgba( 255, 255, 255, ALPHA )';
ctx.lineWidth = WIDTH;
ctx.lineCap = 'round';

function draw()
{
    ctx.beginPath();
    ctx.moveTo( x, y );

    x += STEP * Math.cos( t );
    y += STEP * Math.sin( t );
    t += CURVE * Math.floor( Math.random() * 3 - 1 );
    
    checkEdges();

    ctx.lineTo( x, y );

    ctx.stroke();
}

function checkEdges()
{
    if ( y > (cheight + iheight) / 2 )
    {
        y = (cheight + iheight) / 2;
        t = -t;
    }
    else if ( y < (cheight - iheight) / 2 )
    {
        y = (cheight - iheight) / 2;
        t = -t;
    }

    if ( x > (cwidth + iwidth) / 2 )
    {
        x = (cwidth + iwidth) / 2;
        t = Math.PI - t;
    }
    else if ( x < (cwidth - iwidth) / 2 )
    {
        x = (cwidth - iwidth) / 2;
        t = Math.PI - t;
    }
}

window.setInterval( draw, DELAY );
