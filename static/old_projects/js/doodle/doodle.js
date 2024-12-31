// fill viewport
var canv = document.getElementById( 'canvas' );
canv.width = window.innerWidth;
canv.height = window.innerHeight;

var width = canv.width;
var height = canv.height;
var x = width / 2.0;
var y = height / 2.0;
var t = 0.0;

var STEP = 1.0;
var CURVE = 0.4;
var DELAY = 0.0; // ms

var ctx = canv.getContext( '2d' );

ctx.strokeRect( 0, 0, width, height );

function draw()
{
    ctx.beginPath();
    ctx.moveTo( x, y );

    x += STEP * Math.cos( t );
    y += STEP * Math.sin( t );
    t += CURVE * Math.floor( Math.random() * 3 - 1 );
    
    check();

    ctx.lineTo( x, y );

    ctx.stroke();
}

function check()
{
    if ( y > height - 1 )
    {
        y = 0;
        ctx.moveTo( x, y );
    }
    else if ( y < 0 )
    {
        y = height - 1;
        ctx.moveTo( x, y );
    }

    if ( x > width - 1 )
    {
        x = 0;
        ctx.moveTo( x, y );
    }
    else if ( x < 0 )
    {
        x = width - 1;
        ctx.moveTo( x, y );
    }
}

window.setInterval( draw, DELAY );
